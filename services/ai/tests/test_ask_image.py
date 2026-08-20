"""图片询盘接口测试（mock OCR 与检索，不访问真实模型/数据库/LLM）。"""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.rag.chain import SYSTEM_PROMPT
from app.routers import ask

QUESTION = "这是技术规格参数截图，请帮忙分析是否有匹配的产品，有的话输出产品型号以及价格"


def _client() -> TestClient:
    test_app = FastAPI()
    test_app.include_router(ask.router)
    return TestClient(test_app)


def test_ask_image_fallback_without_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_base_url", None)
    monkeypatch.setattr("app.ocr.ocr_image", lambda content: "额定电压 380V\n功率 5.5kW")
    monkeypatch.setattr(
        "app.routers.ask._retrieve",
        lambda query: [{"text": "产品变频器 型号VFD-220 价格5800.00CNY", "source": "kb_quotes"}],
    )
    resp = _client().post(
        "/api/ask/image",
        data={"question": QUESTION},
        files={"image": ("spec.png", b"fake-bytes", "image/png")},
    )
    assert resp.status_code == 200
    assert "VFD-220" in resp.text
    assert "[DONE]" in resp.text


def test_ask_image_rejects_wrong_type(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = _client().post(
        "/api/ask/image",
        data={"question": QUESTION},
        files={"image": ("spec.txt", b"not-an-image", "text/plain")},
    )
    assert resp.status_code == 400
    assert "仅支持" in resp.json()["detail"]


def test_ask_image_rejects_oversize(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = _client().post(
        "/api/ask/image",
        data={"question": QUESTION},
        files={"image": ("spec.png", b"x" * (ask.MAX_IMAGE_BYTES + 1), "image/png")},
    )
    assert resp.status_code == 400
    assert "5MB" in resp.json()["detail"]


def test_ask_image_rejects_empty_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ocr.ocr_image", lambda content: "")
    resp = _client().post(
        "/api/ask/image",
        data={"question": QUESTION},
        files={"image": ("spec.png", b"fake-bytes", "image/png")},
    )
    assert resp.status_code == 400
    assert "未识别到文字" in resp.json()["detail"]


def test_ask_image_forwards_ocr_text_to_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    async def fake_stream_answer(
        question: str,
        contexts: list[dict[str, str]],
        base_url: str | None,
        model: str,
        api_key: str | None,
        reasoning_effort: str | None = None,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> AsyncIterator[str]:
        del contexts, base_url, model, api_key, reasoning_effort, system_prompt
        captured["question"] = question
        yield "ok"

    monkeypatch.setattr("app.ocr.ocr_image", lambda content: "额定电压 380V\n功率 5.5kW")
    monkeypatch.setattr("app.routers.ask._retrieve", lambda query: [])
    monkeypatch.setattr("app.routers.ask.stream_answer", fake_stream_answer)
    resp = _client().post(
        "/api/ask/image",
        data={"question": QUESTION},
        files={"image": ("spec.png", b"fake-bytes", "image/png")},
    )
    assert resp.status_code == 200
    assert "额定电压 380V" in captured["question"]
    assert QUESTION in captured["question"]
