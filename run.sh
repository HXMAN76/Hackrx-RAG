#!/bin/bash

# Step 1: Check if Qdrant container exists
if [ "$(docker ps -a -q -f name=qdrant)" ]; then
    echo "Qdrant container exists."
    # Step 2: Check if it's running
    if [ "$(docker inspect -f '{{.State.Running}}' qdrant)" != "true" ]; then
        echo "Starting existing Qdrant container..."
        docker start qdrant
    else
        echo "Qdrant is already running."
    fi
else
    echo "Creating and starting new Qdrant container..."
    docker run -d --name qdrant \
        -p 6333:6333 -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant
fi

# Step 3: Run FastAPI app using Uvicorn
echo "Starting FastAPI app..."
uvicorn app.main:app --port 8000 --reload
