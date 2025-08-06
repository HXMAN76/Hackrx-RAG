#!/bin/bash

# Check if qdrant container is already running
if [ "$(docker ps -q -f name=qdrant)" ]; then
    echo "Qdrant already running."
else
    echo "Starting Qdrant..."
    docker-compose up -d qdrant
fi

# Start backend
docker-compose up -d backend
