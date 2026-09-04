import pytest

from vectorstores.pinecone_store import PineconeStore


class FakeIndex:
    def __init__(self):
        self.upsert_calls = []
        self.delete_calls = []
        self.delete_all = False

    def upsert(self, vectors):
        self.upsert_calls.append(vectors)

    def delete(self, ids=None, delete_all=False, filter=None):
        self.delete_all = delete_all
        self.delete_calls.append({"ids": ids, "delete_all": delete_all, "filter": filter})

    def query(self, vector, top_k, include_metadata):
        return {"matches": []}


class FakePinecone:
    def __init__(self, api_key):
        self.api_key = api_key
        self.index = FakeIndex()
        self.indexes = [{"name": "rag-pipeline-index"}]

    def list_indexes(self):
        return self.indexes

    def create_index(self, **kwargs):
        self.created = kwargs

    def Index(self, name):
        return self.index


def test_reset_on_ingest_clears_existing_vectors(monkeypatch):
    fake_pc = FakePinecone("test-key")
    monkeypatch.setattr("vectorstores.pinecone_store.Pinecone", lambda api_key: fake_pc)

    store = PineconeStore(
        api_key="test-key",
        index_name="rag-pipeline-index",
        dimension=3,
        reset_on_ingest=True,
    )

    store.upsert(
        [
            {"text": "first chunk", "metadata": {"source": "A", "page": 1}},
            {"text": "second chunk", "metadata": {"source": "B", "page": 2}},
        ],
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    )

    assert fake_pc.index.delete_all is True
    assert len(fake_pc.index.upsert_calls) >= 1
