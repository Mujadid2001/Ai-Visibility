#!/bin/bash
# Setup script for AI Visibility API

set -e

echo "🚀 AI Visibility Intelligence API - Setup"
echo "=========================================="

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Copy .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from .env.example"
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY"
else
    echo "✓ .env file already exists"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 << EOF
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("✓ Database initialized")
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: python run.py"
echo "3. Visit: http://localhost:5000/health"
echo ""
