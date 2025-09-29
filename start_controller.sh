#!/bin/bash
# Activate virtual environment
source /home/rwb/control/venv/bin/activate

# Run Python script
exec python3 /home/rwb/control/controller.py &
exec python /home/rwb/control/heartbeat.py 
