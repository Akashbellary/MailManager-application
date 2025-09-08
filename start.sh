#!/bin/bash

# Get the port from environment variable or default to 10000
PORT=${PORT:-10000}

# Start gunicorn with the correct port
echo "Starting gunicorn on port $PORT"
exec gunicorn --bind 0.0.0.0:$PORT app:app