import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import db
from app.config import settings
from app.embeddings import embed_texts
from app.rag.chain import stream_answer

router = APIRouter(prefix="/api", tags=["ask"])

TOP_K = 5


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def _retrieve(question: str) -> list[dict[str, str]]:
    """问题向量化 → pgvector 检索文档分块与报价各 top-5"""
    try:
        query_vector = embed_texts([question], settings.embed_model)[0]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"向量化失败: {exc}") from exc
    try:
        return db.search_documents(query_vector, TOP_K) + db.search_quotes(query_vector, TOP_K)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"向量检索失败: {exc}") from exc


async def _sse(body: AskRequest, contexts: list[dict[str, str]]) -> AsyncIterator[str]:
    """SSE 事件流：每个 token 一个 data 事件，以 [DONE] 结束"""
    async for token in stream_answer(
        question=body.question,
        contexts=contexts,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        reasoning_effort=settings.llm_reasoning_effort,
    ):
        yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/ask/stream")
def ask_stream(body: AskRequest) -> StreamingResponse:
    """流式问答：本地向量检索 + LLM 生成（未配置 LLM 时直接返回检索资料）"""
    contexts = _retrieve(body.question)
    return StreamingResponse(_sse(body, contexts), media_type="text/event-stream")
