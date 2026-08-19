import pytest

from app.embeddings import client as embed_client


class _FakeVec:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class _FakeModel:
    def embed(self, texts: list[str]) -> list[_FakeVec]:
        assert len(texts) == 2
        return [_FakeVec([0.0, 1.0]), _FakeVec([1.0, 0.0])]


def test_embed_texts_uses_loaded_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(embed_client, "_model", _FakeModel())
    vectors = embed_client.embed_texts(["你好", "世界"], "fake-model")
    assert vectors == [[0.0, 1.0], [1.0, 0.0]]
