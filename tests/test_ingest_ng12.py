import importlib
import sys
import types


def make_fake_modules():
    # chromadb fake
    chromadb = types.ModuleType("chromadb")

    class FakeCollection:
        def __init__(self):
            self.add_called = False
            self.add_kwargs = None

        def add(self, **kwargs):
            self.add_called = True
            self.add_kwargs = kwargs

    class FakeClient:
        def __init__(self, path=None):
            self.path = path
            self._col = FakeCollection()
            # expose the last client and collection on the chromadb module for assertions
            chromadb._last_client = self
            chromadb._last_collection = self._col

        def get_or_create_collection(self, name):
            self.col_name = name
            return self._col

    chromadb.PersistentClient = FakeClient

    # vertexai fake (package + preview + language_models)
    vertexai = types.ModuleType("vertexai")
    preview = types.ModuleType("vertexai.preview")
    lm = types.ModuleType("vertexai.preview.language_models")

    class FakeTextEmbeddingModel:
        @staticmethod
        def from_pretrained(name):
            class Inst:
                def get_embeddings(self, docs):
                    # return objects with `.values` attribute per doc
                    return [types.SimpleNamespace(values=[len(d)]) for d in docs]

            return Inst()

    lm.TextEmbeddingModel = FakeTextEmbeddingModel
    preview.language_models = lm
    vertexai.preview = preview

    # tiktoken fake
    tiktoken = types.ModuleType("tiktoken")

    class FakeEncoding:
        def encode(self, text):
            return list(text)

        def decode(self, tokens):
            return "".join(tokens)

    def get_encoding(name):
        return FakeEncoding()

    tiktoken.get_encoding = get_encoding

    # pypdf fake
    pypdf = types.ModuleType("pypdf")

    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakePdfReader:
        def __init__(self, path):
            self.pages = [FakePage("one two three"), FakePage("")]

    pypdf.PdfReader = FakePdfReader

    # inject into sys.modules
    sys.modules["chromadb"] = chromadb
    sys.modules["vertexai"] = vertexai
    sys.modules["vertexai.preview"] = preview
    sys.modules["vertexai.preview.language_models"] = lm
    sys.modules["tiktoken"] = tiktoken
    sys.modules["pypdf"] = pypdf


def test_persist_to_chroma_calls_collection_add(tmp_path):
    make_fake_modules()

    # import module after fakes in place
    import ingestion.ingest_ng12 as mod
    importlib.reload(mod)

    # Prepare sample data
    docs = ["a", "b"]
    embs = [[1], [2]]
    metas = [{"m": 1}, {"m": 2}]
    ids = ["id1", "id2"]

    # Call persist_to_chroma
    mod.persist_to_chroma(docs, embs, metas, ids, vector_store_dir=tmp_path, collection_name="testcol")

    # Verify that the underlying fake collection got add called
    chromadb_mod = sys.modules["chromadb"]
    last_col = getattr(chromadb_mod, "_last_collection")
    assert last_col.add_called
    assert last_col.add_kwargs["documents"] == docs
    assert last_col.add_kwargs["embeddings"] == embs
    assert last_col.add_kwargs["metadatas"] == metas
    assert last_col.add_kwargs["ids"] == ids


def test_embed_documents_uses_model_and_returns_vectors():
    make_fake_modules()
    import ingestion.ingest_ng12 as mod
    importlib.reload(mod)

    docs = ["hello", "world!"]
    vectors = mod.embed_documents(docs, model_name="fake-model", batch_size=1)

    # Each vector is [len(doc)] per FakeTextEmbeddingModel
    assert vectors == [[5], [6]]
