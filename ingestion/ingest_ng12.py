import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
from pypdf import PdfReader
import chromadb
import tiktoken
from app.config import DATA_DIR, VECTOR_STORE_DIR, GCP_PROJECT, GCP_REGION, EMBEDDING_MODEL_NAME
from app.vertexai_utils import init_vertexai


def chunk_text_tokens(text, max_tokens=1000, overlap_tokens=100):
    """
    Split text into chunks safely using token count for Vertex embeddings.
    """
    encoding = tiktoken.get_encoding("cl100k_base")  # compatible with Vertex models
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += max_tokens - overlap_tokens
    return chunks



# Helper to batch large lists
def batch(iterable, batch_size=250):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]



def main():
    init_vertexai()

    pdf_path = DATA_DIR / "ng12.pdf"

    documents, metadatas, ids = load_and_chunk_pdf(pdf_path)

    print(f"Total chunks: {len(documents)}")
    if documents:
        print(f"Max chunk length (words): {max(len(c.split()) for c in documents)}")

    embeddings = embed_documents(documents, EMBEDDING_MODEL_NAME)

    persist_to_chroma(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
        vector_store_dir=VECTOR_STORE_DIR,
        collection_name="ng12",
    )

    print("NG12 ingestion complete.")



def load_and_chunk_pdf(pdf_path):
    """Read PDF at `pdf_path` and return (documents, metadatas, ids)."""
    reader = PdfReader(str(pdf_path))

    documents = []
    metadatas = []
    ids = []

    chunk_id = 0

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue

        page_chunks = chunk_text_tokens(text)

        for chunk in page_chunks:
            documents.append(chunk)
            metadatas.append({
                "source": "NG12 PDF",
                "page": page_num + 1,
                "chunk_id": f"ng12_{page_num+1:04d}_{chunk_id:02d}"
            })
            ids.append(f"chunk-{chunk_id}")
            chunk_id += 1

    return documents, metadatas, ids


def embed_documents(documents, model_name, batch_size=250):
    """Return a list of embedding vectors (lists) for `documents`."""
    if not documents:
        return []

    embedding_model = TextEmbeddingModel.from_pretrained(model_name)
    all_vectors = []

    for doc_batch in batch(documents, batch_size=batch_size):
        print(f"Embedding batch of {len(doc_batch)} chunks...")
        batch_embeddings = embedding_model.get_embeddings(doc_batch)
        all_vectors.extend([e.values for e in batch_embeddings])

    return all_vectors


def persist_to_chroma(documents, embeddings, metadatas, ids, vector_store_dir, collection_name="ng12"):
    client = chromadb.PersistentClient(path=str(vector_store_dir))
    collection = client.get_or_create_collection(collection_name)

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )



if __name__ == "__main__":
    main()
