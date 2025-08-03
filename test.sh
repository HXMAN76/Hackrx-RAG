#!/bin/bash

# Exit on error
set -e

# API Endpoint
URL="http://localhost:8000/api/v1/hackrx/document"

# Payload (replace with actual URL you want to fetch)
JSON_PAYLOAD='{
  "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
}'

# Optional: Replace with your real API key if needed
API_KEY="a692774361df87466df8df0cbdecb1a9daca509b1a31d0948aad64b7b3ae5f12"

echo "Sending POST request to $URL..."

curl -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "Authorization: Bearer $API_KEY" \
     -d "$JSON_PAYLOAD" \
     --verbose

echo -e "\n✅ curl test completed."
