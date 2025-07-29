# HackRx RAG System

A modular, high-performance RAG (Retrieval-Augmented Generation) system with sub-30s document processing time.

## 🧱 Architecture

- **PDF Parsing**: PyMuPDF (fitz) for efficient text extraction
- **Embeddings**: Sentence Transformers (bge-base-en-v1.5)
- **Vector DB**: Qdrant Cloud (768d COSINE similarity)
- **LLM Inference**: Groq API (llama-3.1-8b-instant)
- **API**: FastAPI with async endpoints

## 🚀 Features

- Asynchronous document processing pipeline
- Efficient chunking algorithms (size-based and paragraph-based)
- High-quality text embeddings with Sentence Transformers
- Vector search with Qdrant for semantic retrieval
- LLM-powered response generation with context
- Fully containerized for easy deployment
- Sub-30 second processing time for average-sized documents

## 📋 Setup & Installation

### Prerequisites

- Python 3.11+
- Docker (optional)
- [Groq](https://groq.com/) API key for LLM access
- Qdrant Cloud account or local Qdrant instance

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
QDRANT_URL=https://your-qdrant-instance.qdrant.tech
QDRANT_API_KEY=your-api-key
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3
```

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hackrx-rag.git
cd hackrx-rag
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t hackrx-rag:latest .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 --env-file .env --name hackrx-rag hackrx-rag:latest
```

## 🔍 API Usage

### Authentication

All endpoints require authentication using either:
1. Bearer Token: `Authorization: Bearer <token>`
2. API Key: `X-API-Key: <api-key>` 

### RAG Endpoint (Single or Batch)

```http
POST /hackrx/run
```

The /hackrx/run endpoint supports both formats for flexibility:

#### Format 1: Single Query (Standard)

Request body:
```json
{
  "query": "What are the main advantages of RAG systems?",
  "doc_url": "https://example.com/document.pdf",
  "top_k": 3
}
```

#### Format 2: Batch Query (Alternative, also supported by /run endpoint)

Request body:
```json
{
  "documents": "https://example.com/document.pdf",
  "questions": [
    "What are the main advantages of RAG systems?",
    "How do RAG systems handle context retrieval?"
  ],
  "top_k": 3
}
```

Example curl command:

```bash
curl -X POST http://localhost:8000/hackrx/run \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer a692774361df87466df8df0cbdecb1a9daca509b1a31d0948aad64b7b3ae5f12" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
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
```

Response:
```json
{
  "answer": "RAG systems have several advantages...",
  "sources": [
    {
      "text": "Retrieval-Augmented Generation (RAG) combines...",
      "metadata": {
        "url": "https://example.com/document.pdf",
        "chunk_id": 5
      },
      "score": 0.92
    }
  ],
  "processing_time": 1.45
}
```

### Batch RAG Endpoint (Multiple Questions)

> **IMPORTANT**: For batch processing, you MUST use the `/hackrx/batch` endpoint, NOT the `/hackrx/run` endpoint.

```http
POST /hackrx/batch
```

Request body:
```json
{
  "documents": "https://example.com/document.pdf",
  "questions": [
    "What are the main advantages of RAG systems?",
    "How do RAG systems handle context retrieval?"
  ],
  "top_k": 3
}
```

Example curl command:

```bash
curl -X POST http://localhost:8000/hackrx/batch \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer <auth_api>" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
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
```

Response:
```json
{
  "answers": [
    {
      "answer": "RAG systems have several advantages...",
      "sources": [...],
      "processing_time": 1.25
    },
    {
      "answer": "RAG systems handle context retrieval by...",
      "sources": [...],
      "processing_time": 1.30
    }
  ],
  "total_processing_time": 2.55
}
```

### Health Check

```http
GET /hackrx/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## ⚙️ Configuration

Key configuration parameters in `app/config.py`:

- `CHUNK_SIZE`: Size of text chunks (default: 300)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `EMBEDDING_MODEL_NAME`: Sentence Transformer model
- `TOP_K_RETRIEVAL`: Number of chunks to retrieve (default: 3)
- `VECTOR_SIZE`: Embedding vector size (768 for bge-base-en-v1.5)
- `VECTOR_DISTANCE`: Distance metric for vector comparison

## 🧪 Performance Optimization

To maintain sub-30s processing time:

1. Asynchronous document downloading and processing
2. Efficient chunking strategies
3. Pre-loaded embedding model at startup
4. Connection pooling for Qdrant

## 📈 Scaling

For higher workloads:
- Deploy behind a load balancer
- Increase worker count with Gunicorn
- Use a more powerful instance for the embedding model
- Consider horizontal scaling with Kubernetes

## 🔐 Security

Currently implements basic security:
- Optional API key authentication
- CORS protection
- Rate limiting (with slowapi)

Additional security measures can be added in production.

## 📝 License

[MIT License](LICENSE)
