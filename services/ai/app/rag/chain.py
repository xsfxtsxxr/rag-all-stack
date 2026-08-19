import json
from collections.abc import AsyncIterator
from typing import Any, TypedDict, cast

import httpx

SYSTEM_PROMPT = (
    "你是一名工业销售询盘知识库助手。请基于给定的知识库片段回答用户问题，"
    "回答中必须引用相关产品的型号与报价，并注明价格有效期。"
    "如果片段中没有相关信息，请明确说明，不要编造。"
)


def build_context(contexts: list[dict[str, str]]) -> str:
    """把检索到的片段拼成带来源标注的上下文"""
    blocks: list[str] = []
    for index, ctx in enumerate(contexts, start=1):
        source = ctx.get("source", "未知来源")
        text = ctx.get("text", "").strip()
        if text:
            blocks.append(f"[{index}] 来源: {source}\n{text}")
    return "\n\n".join(blocks)


class _StreamDelta(TypedDict, total=False):
    """OpenAI 兼容流式响应 chunk 中的 delta 部分"""

    content: str


class _StreamChoice(TypedDict, total=False):
    """OpenAI 兼容流式响应 chunk 中的单个 choice"""

    delta: _StreamDelta


class _StreamChunk(TypedDict, total=False):
    """OpenAI 兼容流式响应的单个 SSE chunk"""

    choices: list[_StreamChoice]


class LLMError(Exception):
    """LLM 接口调用失败（非 2xx 状态码或网络错误）"""


async def _stream_llm(
    base_url: str,
    model: str,
    api_key: str | None,
    context_text: str,
    question: str,
    reasoning_effort: str | None = None,
) -> AsyncIterator[str]:
    """调用 OpenAI 兼容接口的流式 chat/completions，逐 token 产出

    失败（非 2xx 状态码、网络错误）时抛出 LLMError，由上层降级处理。
    reasoning_effort 非空时（low/high/max）附加 thinking 与 reasoning_effort 参数，
    供 GLM-5.x 等推理型模型使用。
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"知识库片段：\n{context_text}\n\n用户问题：{question}",
            },
        ],
    }
    if reasoning_effort:
        # 推理型模型（如 glm-5.3）必须开启 thinking；low 档可减少推理耗时与消耗
        payload["thinking"] = {"type": "enabled"}
        payload["reasoning_effort"] = reasoning_effort
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        async with (
            httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client,
            client.stream("POST", url, json=payload, headers=headers) as resp,
        ):
            if resp.status_code != 200:
                body = (await resp.aread()).decode("utf-8", "replace").strip()
                raise LLMError(f"LLM 接口返回 {resp.status_code}: {body[:200]}")
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                try:
                    raw = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if not isinstance(raw, dict):
                    continue
                parsed = cast(_StreamChunk, raw)
                choices = parsed.get("choices")
                if not choices:
                    continue
                delta = choices[0].get("delta")
                if not isinstance(delta, dict):
                    continue
                token = delta.get("content")
                if isinstance(token, str) and token:
                    yield token
    except httpx.HTTPError as exc:
        raise LLMError(f"LLM 接口请求失败: {exc}") from exc


async def stream_answer(
    question: str,
    contexts: list[dict[str, str]],
    base_url: str | None,
    model: str,
    api_key: str | None,
    reasoning_effort: str | None = None,
) -> AsyncIterator[str]:
    """流式生成回答。

    未配置 LLM_BASE_URL，或 LLM 调用失败时降级：直接把检索到的资料返回给用户，
    保证系统在无可用大模型的环境下也能跑通。
    """
    context_text = build_context(contexts)

    if not base_url:
        if not context_text:
            yield "知识库中没有检索到相关内容，请补充文档或调整问题。"
            return
        yield "以下是与问题相关的知识库资料（未配置 LLM，可设置 LLM_BASE_URL 启用生成式回答）：\n\n"
        yield context_text
        return

    try:
        async for token in _stream_llm(
            base_url, model, api_key, context_text, question, reasoning_effort
        ):
            yield token
    except LLMError as exc:
        if not context_text:
            yield f"LLM 生成失败（{exc}），且知识库中没有检索到相关内容。"
            return
        yield f"（LLM 生成失败：{exc}）\n\n以下是与问题相关的知识库资料：\n\n"
        yield context_text
