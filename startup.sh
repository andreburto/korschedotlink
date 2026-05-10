#!/bin/bash

# Kirsche API Server Startup Script
# This script finds a Python interpreter, loads environment variables, and starts the server.

set -e  # Exit on error

echo "=========================================="
echo "Kirsche API Server Startup"
echo "=========================================="
echo ""

# ============================================
# Step 1: Find Python Interpreter
# ============================================
echo "Step 1: Finding Python interpreter..."

PYTHON_CMD=""

# Try python3.11 first
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✓ Found python3.11 at: $(which python3.11)"
# Try python3 next
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✓ Found python3 at: $(which python3)"
# Try python last
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✓ Found python at: $(which python)"
else
    echo "✗ Error: No Python interpreter found!"
    echo "  Please install Python 3.x"
    exit 1
fi

# Verify Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "  Python version: $PYTHON_VERSION"
echo ""

# ============================================
# Step 2: Load Environment Variables
# ============================================
echo "Step 2: Loading environment variables from .env..."

# Check if .env file exists
if [[ ! -f .env ]]; then
    echo "✗ Error: .env file not found!"
    echo "  Please create a .env file in the project root"
    exit 1
fi

# Load environment variables from .env file
# This will export all non-comment, non-empty lines
set -a  # Automatically export all variables
source .env
set +a  # Stop automatically exporting

echo "✓ Environment variables loaded from .env"
echo ""

# Confirm each variable is set
echo "Confirming environment variables..."

# Extract variable names from .env (excluding comments and empty lines)
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | cut -d '=' -f 1 | xargs)

# Check each variable
for VAR in $ENV_VARS; do
    if env | grep -q "^${VAR}="; then
        # Get the value (mask sensitive data)
        VALUE=$(env | grep "^${VAR}=" | cut -d '=' -f 2-)
        # Mask API keys and secrets
        if [[ $VAR == *"KEY"* ]] || [[ $VAR == *"SECRET"* ]]; then
            echo "  ✓ $VAR=***MASKED***"
        else
            echo "  ✓ $VAR=$VALUE"
        fi
    else
        echo "  ✗ $VAR is not set!"
    fi
done

echo ""

# ============================================
# Step 3: Start the Server
# ============================================
echo "Step 3: Starting Kirsche API Server..."
echo "=========================================="
echo ""

# Run the server
exec $PYTHON_CMD src/server.py
