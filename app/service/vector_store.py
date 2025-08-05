import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

# Qdrant configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "RAG-Hackrx"
VECTOR_SIZE = 768  # Matches BGE model

# Initialize client
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_collection(overwrite: bool = False):
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        if overwrite:
            client.delete_collection(collection_name=COLLECTION_NAME)
            logging.info(f"⚠️ Overwriting existing collection '{COLLECTION_NAME}'")
        else:
            logging.info(f"ℹ️ Collection '{COLLECTION_NAME}' already exists.")
            return
    except Exception:
        logging.info(f"ℹ️ Collection '{COLLECTION_NAME}' does not exist. Creating...")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"✅ Collection '{COLLECTION_NAME}' is ready.")


def upload_qdrant_ready_file(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        points_raw = json.load(f)

    points = [
        PointStruct(id=pt["id"], vector=pt["vector"], payload=pt["payload"])
        for pt in points_raw
    ]
    
    init_collection(True)
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logging.info(f"✅ Uploaded {len(points)} vectors to Qdrant collection '{COLLECTION_NAME}'.")
