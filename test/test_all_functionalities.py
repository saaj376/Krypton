import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Temporarily point to the local sdk_build directory so we don't need to pip install it before running tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../sdk_build')))
from krypton_sdk import KryptonClient
import httpx

class TestKryptonSDK(unittest.TestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.base_url = "http://localhost:8000"
        self.client = KryptonClient(email=self.email, base_url=self.base_url)

    def test_init_validation(self):
        """Test SDK initialization with missing arguments."""
        with self.assertRaises(ValueError):
            KryptonClient(email="", base_url=self.base_url)
        with self.assertRaises(ValueError):
            KryptonClient(email=self.email, base_url="")

    @patch("krypton_sdk.httpx.post")
    def test_join_queue_success(self, mock_post):
        """Test successful join_queue fetching an API key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "api_key": "test_api_key"}
        mock_post.return_value = mock_response

        self.client.join_queue()
        
        self.assertEqual(self.client.api_key, "test_api_key")
        mock_post.assert_called_once_with(
            f"{self.base_url}/join-queue",
            json={"user_email": self.email},
            timeout=15.0
        )

    @patch("krypton_sdk.httpx.post")
    def test_join_queue_waitlist(self, mock_post):
        """Test join_queue when user is placed on a waitlist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "waitlist"}
        mock_post.return_value = mock_response

        self.client.join_queue()
        self.assertIsNone(self.client.api_key)

    @patch("krypton_sdk.httpx.post")
    def test_join_queue_offline_fallback(self, mock_post):
        """Test join_queue gracefully falls back when gateway server is offline."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        with patch.object(self.client, '_notify_offline_server') as mock_notify:
            self.client.join_queue()
            mock_notify.assert_called_once()

    @patch("krypton_sdk.httpx.post")
    def test_generate_non_streaming(self, mock_post):
        """Test generate with stream=False."""
        self.client.api_key = "valid_key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is a non-stream response."}
        mock_post.return_value = mock_response

        result = self.client.generate("Hello", stream=False)
        self.assertEqual(result, "This is a non-stream response.")
        
        mock_post.assert_called_once_with(
            f"{self.base_url}/generate",
            json={
                "prompt": "Hello", 
                "model": "llama3", 
                "max_tokens": 100, 
                "temperature": 0.7, 
                "stream": False
            },
            headers={"X-API-Key": "valid_key"},
            timeout=120.0
        )

    @patch("krypton_sdk.httpx.stream")
    def test_generate_streaming(self, mock_stream):
        """Test generate with stream=True."""
        self.client.api_key = "valid_key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            '{"response": "streaming "}',
            '{"response": "works!"}'
        ]
        
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_stream.return_value = mock_context_manager

        stream_gen = self.client.generate("Hello", stream=True)
        chunks = list(stream_gen)
        
        self.assertEqual(chunks, ["streaming ", "works!"])
        mock_stream.assert_called_once_with(
            "POST",
            f"{self.base_url}/generate",
            json={
                "prompt": "Hello", 
                "model": "llama3", 
                "max_tokens": 100, 
                "temperature": 0.7, 
                "stream": True
            },
            headers={"X-API-Key": "valid_key"},
            timeout=120.0
        )

    def test_generate_without_api_key(self):
        """Test generating text without joining the queue first (missing API key)."""
        result = self.client.generate("Hello")
        self.assertIsNone(result)

    @patch("krypton_sdk.httpx.post")
    def test_generate_offline_fallback(self, mock_post):
        """Test gateway being offline when generating text gracefully alerts server."""
        self.client.api_key = "valid_key"
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        with patch.object(self.client, '_notify_offline_server') as mock_notify:
            result = self.client.generate("Hello")
            self.assertIsNone(result)
            mock_notify.assert_called_once()

    @patch("krypton_sdk.httpx.post")
    def test_generate_unauthorized(self, mock_post):
        """Test gateway generation when API key is expired or invalid."""
        self.client.api_key = "expired_key"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = self.client.generate("Hello", stream=False)
        self.assertIsNone(result)

    @patch("krypton_sdk.httpx.stream")
    def test_generate_streaming_unauthorized(self, mock_stream):
        """Test gateway generation (streaming) when API key is expired or invalid."""
        self.client.api_key = "expired_key"
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_stream.return_value = mock_context_manager

        stream_gen = self.client.generate("Hello", stream=True)
        # Because we yield instead of parsing direct exception from 401, stream returns generator 
        # but 401 will just cause streaming to immediately exit (print Invalid API key).
        chunks = list(stream_gen)
        self.assertEqual(chunks, [])

    @patch("krypton_sdk.httpx.post")
    def test_notify_offline_server_success(self, mock_post):
        """Test the ping server mechanism when primary gateway is off."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.client._notify_offline_server()
        
        mock_post.assert_called_once_with(
            "https://krypton-pl4h.onrender.com/request-access",
            json={"user_email": self.email},
            timeout=10.0
        )

    @patch("krypton_sdk.httpx.post")
    def test_notify_offline_server_failure(self, mock_post):
        """Test that ping server failure doesn't crash the SDK."""
        mock_post.side_effect = Exception("Network unreachable")
        
        try:
            self.client._notify_offline_server()
        except Exception:
            self.fail("_notify_offline_server() raised Exception unexpectedly!")

if __name__ == '__main__':
    unittest.main()
