#!/bin/bash
echo "Building project..."

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Collect static files
python3 manage.py collectstatic --noinput --clear

echo "Build finished!"
