import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import db
from app.config import settings
from app.embeddings import embed_texts
from app.rag.chain import SPEC_SYSTEM_PROMPT, SYSTEM_PROMPT, stream_answer

router = APIRouter(prefix="/api", tags=["ask"])

TOP_K = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
DEFAULT_IMAGE_QUESTION = (
    "这是技术规格参数截图，请帮忙分析是否有匹配的产品，有的话输出产品型号以及价格"
)


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


async def _sse(
    question: str,
    contexts: list[dict[str, str]],
    system_prompt: str = SYSTEM_PROMPT,
) -> AsyncIterator[str]:
    """SSE 事件流：每个 token 一个 data 事件，以 [DONE] 结束"""
    async for token in stream_answer(
        question=question,
        contexts=contexts,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        reasoning_effort=settings.llm_reasoning_effort,
        system_prompt=system_prompt,
    ):
        yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/ask/stream")
def ask_stream(body: AskRequest) -> StreamingResponse:
    """流式问答：本地向量检索 + LLM 生成（未配置 LLM 时直接返回检索资料）"""
    contexts = _retrieve(body.question)
    return StreamingResponse(_sse(body.question, contexts), media_type="text/event-stream")


@router.post("/ask/image")
def ask_image(
    image: Annotated[UploadFile, File(description="技术规格参数截图")],
    question: Annotated[str, Form()] = DEFAULT_IMAGE_QUESTION,
) -> StreamingResponse:
    """图片询盘：OCR 提取规格参数 → 向量检索 → 流式生成产品型号与价格推荐"""
    from app.ocr import ocr_image  # 延迟导入：避免服务启动即加载 OCR 模型依赖

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/webp/bmp 格式图片")
    content = image.file.read()
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")
    try:
        spec_text = ocr_image(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not spec_text:
        raise HTTPException(status_code=400, detail="图片中未识别到文字内容")
    contexts = _retrieve(spec_text)
    # 检索用 OCR 参数做 query；生成时把参数原文一并交给 LLM 做规格比对
    question_with_spec = f"{question}\n\n截图 OCR 提取的规格参数：\n{spec_text}"
    return StreamingResponse(
        _sse(question_with_spec, contexts, SPEC_SYSTEM_PROMPT),
        media_type="text/event-stream",
    )
