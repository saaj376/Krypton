import sys
import os
import unittest

# Add project root to path so we can import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import init_db, create_key, validate_key, delete_expired_keys, get_connection

class TestDatabase(unittest.TestCase):

    def setUp(self):
        # 1. Initialize logic before EACH test
        init_db()

    def test_key_lifecycle_and_persistence(self):
        # 2. Create a valid key (3 hours)
        key_valid = "valid-key-123"
        create_key(key_valid, "Tester A", ttl_hours=3)

        # 3. Create an expired key (expired 1 hour ago)
        key_expired = "expired-key-456"
        create_key(key_expired, "Tester B", ttl_hours=-1)

        # 4. Validate
        is_valid = validate_key(key_valid)
        is_expired_valid = validate_key(key_expired)
        self.assertTrue(is_valid, f"Expected '{key_valid}' to be valid, got {is_valid!r}")
        self.assertFalse(is_expired_valid, f"Expected '{key_expired}' to be invalid, got {is_expired_valid!r}")

        # 5. Cleanup
        delete_expired_keys()

        # 6. Verify cleanup
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key_string FROM api_keys")
            keys = [row[0] for row in cursor.fetchall()]

        self.assertEqual(
            keys,
            [key_valid],
            f"Expected remaining keys to be ['{key_valid}'], got {keys!r}",
        )

        # 7. Persistence Test - Re-connect to ensure data is still there
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM api_keys")
            row = cursor.fetchone()

        self.assertIsNotNone(row, "Expected at least one row for key count query, got None")
        count = row[0]
        # After running key lifecycle tests, we expect at least one key to persist.
        self.assertGreaterEqual(
            count,
            1,
            f"Expected at least one key to persist in the database, got count={count!r}",
        )


if __name__ == "__main__":
    unittest.main()