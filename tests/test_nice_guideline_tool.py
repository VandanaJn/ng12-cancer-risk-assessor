import importlib
import sys
import types


def make_fake_modules():
    # Fake chromadb
    chromadb = types.ModuleType("chromadb")

    class FakeCollection:
        def __init__(self, docs=None):
            self._docs = docs or []

        def query(self, query_embeddings=None, n_results=3):
            return {"documents": [self._docs]}

    class FakeClient:
        def __init__(self, path=None, docs=None):
            self.path = path
            self._collection = FakeCollection(docs)

        def get_collection(self, name):
            return self._collection

    chromadb.PersistentClient = FakeClient
    chromadb._BaseClient = FakeClient

    # Fake vertexai.preview.language_models.TextEmbeddingModel
    vertexai = types.ModuleType("vertexai")
    preview = types.ModuleType("vertexai.preview")
    lm = types.ModuleType("vertexai.preview.language_models")

    class FakeTextEmbeddingModel:
        @staticmethod
        def from_pretrained(name):
            class Inst:
                def get_embeddings(self, docs):
                    # return objects with `.values` attr
                    return [types.SimpleNamespace(values=[len(d)]) for d in docs]

            return Inst()

    lm.TextEmbeddingModel = FakeTextEmbeddingModel
    preview.language_models = lm
    vertexai.preview = preview

    # Fake google adk and vertexai.agent_engines
    google = types.ModuleType("google")
    adk = types.ModuleType("google.adk")
    agents = types.ModuleType("google.adk.agents")
    agents.Agent = object
    adk.agents = agents
    google.adk = adk

    va_agent_engines = types.ModuleType("vertexai.agent_engines")
    va_agent_engines.AdkApp = object

    # inject into sys.modules
    sys.modules["chromadb"] = chromadb
    sys.modules["vertexai"] = vertexai
    sys.modules["vertexai.preview"] = preview
    sys.modules["vertexai.preview.language_models"] = lm
    sys.modules["google"] = google
    sys.modules["google.adk"] = adk
    sys.modules["google.adk.agents"] = agents
    sys.modules["vertexai.agent_engines"] = va_agent_engines

    return chromadb, lm


def test_search_returns_documents_when_found(monkeypatch):
    chromadb_mod, lm_mod = make_fake_modules()

    # Prepare a client that will return docs
    docs = ["Section A: refer if ...", "Section B: urgent ..."]

    # Monkeypatch the PersistentClient to return our client with docs
    def fake_client_factory(path=None):
        return chromadb_mod._BaseClient(path=path, docs=docs)

    chromadb_mod.PersistentClient = fake_client_factory

    # Now import the module
    import app.tools.nice_guideline_tool as ng
    importlib.reload(ng)

    res = ng.search_nice_ng12_guidelines("chest pain")

    assert "Section A" in res
    assert "Section B" in res


def test_search_returns_no_results_when_empty(monkeypatch):
    chromadb_mod, lm_mod = make_fake_modules()

    # Empty docs
    def fake_client_factory(path=None):
        return chromadb_mod._BaseClient(path=path, docs=[])

    chromadb_mod.PersistentClient = fake_client_factory

    import app.tools.nice_guideline_tool as ng
    importlib.reload(ng)

    res = ng.search_nice_ng12_guidelines("nonexistent symptom")

    assert res == "No relevant guideline sections found."
