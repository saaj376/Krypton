#!/bin/bash
# run_tests.sh (Optional)
# A simple script to automatically run the Python test suite that checks all functionalities within the SDK.

echo "======================================================"
echo "   KRYPTON SDK - AUTOMATED TEST SUITE RUNNER"
echo "======================================================"
echo ""

# Ensure we are in the correct root directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please set one up first in the 'venv' directory."
    exit 1
fi

echo "🚀 Running Python SDK Tests (test_all_functionalities.py)..."
echo "Starting..."
echo ""

# Activate the virtual environment and forcefully run the integration testing script
source venv/bin/activate
python3 test/test_all_functionalities.py

# Check test success based on exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All SDK functionalities passed perfectly!"
else
    echo ""
    echo "❌ Tests encountered an error. See the output above."
fi
