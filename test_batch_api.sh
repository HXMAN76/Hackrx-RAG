#!/bin/bash
# Test batch queries against the RAG API

# Base URL
API_URL="http://localhost:8000/api/v1/hackrx/run"

# Auth token
AUTH_TOKEN="a692774361df87466df8df0cbdecb1a9daca509b1a31d0948aad64b7b3ae5f12"

# Document URL (policy PDF)
DOC_URL="https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"

# Send the batch query request
echo "Sending batch query request to $API_URL"
curl -X POST "$API_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "documents": "'"$DOC_URL"'",
    "questions": [
      "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
      "What is the waiting period for pre-existing diseases (PED) to be covered?",
      "Does this policy cover maternity expenses, and what are the conditions?",
      "What is the waiting period for cataract surgery?",
      "Are the medical expenses for an organ donor covered under this policy?",
      "What is the No Claim Discount (NCD) offered in this policy?",
      "Is there a benefit for preventive health check-ups?",
      "How does the policy define a Hospital?",
      "What is the extent of coverage for AYUSH treatments?",
      "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
  }'
