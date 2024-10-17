#!/bin/bash

cd /home/hexazn/api_platform
git pull origin main  # Pull latest changes from Git

# If using a virtual environment
#source /home/hexazn/api_platform/venv/bin/activate

# Install dependencies if there are new ones
pip install -r requirements.txt

# Restart the service
sudo systemctl restart api_platform
