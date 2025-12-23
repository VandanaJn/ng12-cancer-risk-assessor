import chromadb
from vertexai.preview.language_models import TextEmbeddingModel
from app.config import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME

# Initialize Chroma client
client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
print(client.list_collections())

collection = client.get_collection("ng12")
print(f"Items in collection: {collection.count()}")
# Create embedding model
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

# Sample query
query = "What are the urgent referral criteria for dyspepsia?"

# Get query embedding
query_embedding = embedding_model.get_embeddings([query])[0].values

# Search Chroma
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,   # top 3 matches
    include=["documents", "metadatas"]
)

for i, doc in enumerate(results['documents'][0]):
    metadata = results['metadatas'][0][i]
    print(f"\n--- Result {i+1} ---")
    print(f"Page: {metadata['page']}, Chunk ID: {metadata['chunk_id']}")
    print(f"Text excerpt: {doc[:300]}...")  # first 300 chars
