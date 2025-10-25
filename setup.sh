#!/bin/bash

echo "Setting up Expense Tracker..."
echo "=============================="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data
mkdir -p reports
mkdir -p config

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
fi

echo ""
echo "=============================="
echo "✓ Setup complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY (optional, for AI categorization)"
echo "2. Grant Full Disk Access to Terminal (for SMS extraction):"
echo "   System Preferences → Security & Privacy → Privacy → Full Disk Access"
echo "3. Run: source venv/bin/activate"
echo "4. Test: python src/main.py process --help"
echo ""
