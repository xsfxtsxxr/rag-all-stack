from collections.abc import AsyncIterator

import pytest

from app.rag.chain import LLMError, build_context, stream_answer


def test_build_context_skips_empty() -> None:
    context = build_context(
        [
            {"text": "   ", "source": "quotes"},
            {"text": "产品变频器 型号VFD-220 价格5800.00CNY", "source": "kb_quotes"},
        ]
    )
    assert "VFD-220" in context
    assert "来源: kb_quotes" in context


async def test_stream_fallback_without_llm() -> None:
    chunks = [
        c
        async for c in stream_answer(
            "有没有变频器？",
            [{"text": "产品变频器 型号VFD-220 价格5800.00CNY", "source": "kb_quotes"}],
            None,
            "qwen2.5",
            None,
        )
    ]
    assert any("VFD-220" in c for c in chunks)


async def test_stream_empty_context_without_llm() -> None:
    chunks = [c async for c in stream_answer("问题", [], None, "qwen2.5", None)]
    assert "没有检索到相关内容" in "".join(chunks)


async def _fake_stream_llm_raising(
    base_url: str,
    model: str,
    api_key: str | None,
    context_text: str,
    question: str,
    reasoning_effort: str | None = None,
) -> AsyncIterator[str]:
    """模拟 LLM 接口报错（async for 首个 __anext__ 即抛出）"""
    if False:  # 仅用于让本函数成为异步生成器
        yield ""
    raise LLMError("LLM 接口返回 429: 余额不足")


async def test_stream_fallback_on_llm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.rag.chain._stream_llm", _fake_stream_llm_raising)
    chunks = [
        c
        async for c in stream_answer(
            "有没有变频器？",
            [{"text": "产品变频器 型号VFD-220 价格5800.00CNY", "source": "kb_quotes"}],
            "https://open.bigmodel.cn/api/paas/v4",
            "qwen2.5",
            "api-key",
        )
    ]
    joined = "".join(chunks)
    assert "LLM 生成失败" in joined
    assert "VFD-220" in joined


async def test_stream_fallback_on_llm_error_empty_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.rag.chain._stream_llm", _fake_stream_llm_raising)
    chunks = [
        c
        async for c in stream_answer(
            "问题", [], "https://open.bigmodel.cn/api/paas/v4", "qwen2.5", "api-key"
        )
    ]
    joined = "".join(chunks)
    assert "LLM 生成失败" in joined
    assert "没有检索到相关内容" in joined


async def test_stream_passes_reasoning_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    async def fake_stream_llm(
        base_url: str,
        model: str,
        api_key: str | None,
        context_text: str,
        question: str,
        reasoning_effort: str | None = None,
    ) -> AsyncIterator[str]:
        captured["reasoning_effort"] = reasoning_effort
        yield "回答"

    monkeypatch.setattr("app.rag.chain._stream_llm", fake_stream_llm)
    chunks = [
        c
        async for c in stream_answer(
            "问题",
            [{"text": "片段", "source": "kb"}],
            "https://api.z.ai/api/coding/paas/v4",
            "glm-5.3",
            "key",
            "low",
        )
    ]
    assert captured["reasoning_effort"] == "low"
    assert chunks == ["回答"]
