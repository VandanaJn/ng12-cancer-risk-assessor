import chromadb
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from app.config import VECTOR_STORE_DIR, GCP_REGION, EMBEDDING_MODEL_NAME
import os
from vertexai.preview.language_models import TextEmbeddingModel
import chromadb
from app.config import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME

embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

def search_nice_ng12_guidelines(query: str, top_n: int = 5) -> dict:
    """
    Search the local NICE NG12 vector database for relevant guideline excerpts.

    Args:
        query (str): A natural-language query describing patient symptoms
            or clinical criteria (e.g., "unexplained hemoptysis in smoker").
        top_n (int): Maximum number of results to return (default: 5).

    Returns:
        dict: Structured result with "results" list containing {document, metadata}
        pairs, or empty list if no matches found.
        Example:
        {
            "results": [
                {"document": "...", "metadata": {"page": 1, "source": "NG12 PDF", ...}},
                ...
            ]
        }
    """

    # 1. Embed the query using Vertex AI
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # 2. Load persistent ChromaDB
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    collection = client.get_collection("ng12")

    # 3. Vector search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_n,
        include=["documents", "metadatas"]
    )

    # 4. Return structured results with both documents and metadata
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return {"results": []}

    # Pair each document with its metadata
    result_list = [
        {"document": doc, "metadata": meta}
        for doc, meta in zip(documents, metadatas)
    ]

    return {"results": result_list}