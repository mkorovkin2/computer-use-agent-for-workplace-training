#!/bin/bash
set -e

echo "=========================================="
echo "Setting up Training Agent"
echo "=========================================="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate it
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "=========================================="
    echo "IMPORTANT: Edit .env and add your API key!"
    echo "=========================================="
fi

echo ""
echo "Setup complete!"
echo ""
echo "To run the agent:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Open your training platform in a browser and log in"
echo "  3. Run: source venv/bin/activate && python run_agent.py"
echo ""
