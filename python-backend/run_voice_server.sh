#!/bin/bash

# Set UTF-8 encoding for Python and system
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# Start the voice-enabled server
echo "🏠 Starting Housing Authority Assistant with Voice Support"
echo "Setting encoding: UTF-8"
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:3000"

python api_voice_only.py