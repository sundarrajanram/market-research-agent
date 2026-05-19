#!/bin/bash
# Setup script for Market Research Agent

echo "Setting up Market Research Agent..."

cd "$(dirname "$0")"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create reports directory
mkdir -p reports

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Gmail App Password"
echo "   (See README for how to create one)"
echo ""
echo "2. Test the agent:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Run the scheduler:"
echo "   source venv/bin/activate"
echo "   python scheduler.py"
echo ""
echo "4. For production, set up as a systemd service or cron job."
