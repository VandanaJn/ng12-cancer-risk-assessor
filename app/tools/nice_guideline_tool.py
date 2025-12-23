import chromadb
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from app.config import VECTOR_STORE_DIR, GCP_REGION, EMBEDDING_MODEL_NAME
import os
from vertexai.preview.language_models import TextEmbeddingModel
import chromadb
from app.config import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME

embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

def search_nice_ng12_guidelines(query: str) -> str:
    """
    Search the local NICE NG12 vector database for relevant guideline excerpts.

    Args:
        query (str): A natural-language query describing patient symptoms
            or clinical criteria (e.g., "unexplained hemoptysis in smoker").

    Returns:
        str: Concatenated NG12 guideline excerpts suitable for citation-based
        clinical reasoning by the agent.
    """

    # 1. Embed the query using Vertex AI
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # 2. Load persistent ChromaDB
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    collection = client.get_collection("ng12")

    # 3. Vector search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    # 4. Return top chunks as readable text
    documents = results.get("documents", [[]])[0]

    if not documents:
        return "No relevant guideline sections found."

    return "\n\n---\n\n".join(documents)