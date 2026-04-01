#!/bin/bash
# Agency Research Automation — Setup Script
# Owner: Md Jamil Islam
# Usage: bash scripts/setup.sh

set -e

echo "🚀 Setting up Agency Research Automation..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Create necessary directories
mkdir -p logs tracking data/reports data/raw data/exports
echo "✅ Directories created"

# Setup env file
if [ ! -f "config/api_keys.env" ]; then
    cp config/api_keys.env.example config/api_keys.env
    echo "✅ Created config/api_keys.env from template"
    echo "⚠️  Please edit config/api_keys.env with your API keys before running"
fi

# Initialize tracking files
if [ ! -f "tracking/leads.csv" ]; then
    echo "name,niche,location,email,phone,website,status,lead_score,grade,created_at" > tracking/leads.csv
    echo "✅ Initialized tracking/leads.csv"
fi

if [ ! -f "tracking/campaigns.json" ]; then
    echo "[]" > tracking/campaigns.json
    echo "✅ Initialized tracking/campaigns.json"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config/api_keys.env with your API keys"
echo "  2. Run: python scripts/run_research.py --niche restaurant --location 'New York, NY'"
echo "  3. Run: python scripts/send_outreach.py --dry-run"
echo "  4. Run: python scripts/scheduler.py --start"
