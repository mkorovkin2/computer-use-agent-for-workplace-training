#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Run the agent
python run_agent.py
