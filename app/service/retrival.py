from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from typing import List
import numpy as np
import os
from dotenv import load_dotenv
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS
import ast

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Qdrant settings
QDRANT_HOST = os.getenv("QDRANT_URL", "http://localhost:6333").split("://")[-1].split(":")[0]
QDRANT_PORT = 6333
COLLECTION_NAME = "RAG-Hackrx"
TOP_K = 3

# Load model & client
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

from typing import List

from typing import List, Dict

def retrieve_answers(queries: List[str]) -> Dict[str, List[str]]:
    results = {}

    processed_queries = [f"passage: {q}" for q in queries]
    embeddings = model.encode(processed_queries, normalize_embeddings=True)

    for query, emb in zip(queries, embeddings):
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=emb.tolist(),
            limit=3,
            with_payload=True,
        )

        top_chunks = [
            hit.payload.get("text", "No text found.")
            for hit in search_result
        ]

        if not top_chunks:
            top_chunks = ["No relevant answers found."] * 3

        results[query] = top_chunks

    return results


def format_retrieval_results(results: List[List[str]]) -> str:
    """
    Formats the retrieval results into a readable string.
    """
    if not results:
        return "No relevant information found."
    
    formatted = []
    for i, chunks in enumerate(results):
        formatted.append(f"{chunks}")
        
    return formatted

def llm_inference(questions: List[str]) -> dict:
    answers = retrieve_answers(questions)
    prompt = f"""
You are a helpful assistant. Using only the retrieved context chunks, respond to the user's questions.

**Instructions**:
- For each question, synthesize an answer using **only the corresponding list of context chunks**.
- Respond in **a single formal and complete sentence** per question.
- Incorporate **all specific conditions, durations, and clauses** mentioned in the context.
- Use a **professional tone**, reusing **exact phrases** from the chunks wherever possible.
- Do **not** infer or assume any information if provided context doesn't cover it.
- Preserve the **order of questions** in the final output.
- **Return ONLY a Python list of strings** (no extra text, no labels, no numbering).

**Input**:
A dictionary mapping each question to its top 3 context chunks:
{answers}

**Questions**:
{questions}

**Output Format**:
[
    "Answer to question 1...",
    "Answer to question 2...",
    ...
]
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
    )

    # Try parsing the LLM response content into a Python list
    content = response.choices[0].message.content.strip()

    try:
        parsed_answers = ast.literal_eval(content)
        if isinstance(parsed_answers, list) and all(isinstance(ans, str) for ans in parsed_answers):
            return {"answers": parsed_answers}
        else:
            raise ValueError("Response format is invalid.")
    except Exception as e:
        # Fallback response or logging
        return {"answers": [f"Error parsing model response: {e}"]}