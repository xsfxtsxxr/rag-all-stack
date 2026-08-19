"""索引接口：扫描本地文档文件夹并重建 pgvector 索引。"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import db
from app.config import settings
from app.embeddings import embed_texts
from app.parsers import registry
from app.parsers.chunker import split_text

router = APIRouter(prefix="/api", tags=["index"])


class ReindexResponse(BaseModel):
    documents: int
    chunks: int
    quotes: int


class DocumentItem(BaseModel):
    filename: str
    chunkCount: int
    updatedAt: str


def _read_docx_files() -> list[tuple[str, bytes]]:
    """扫描配置目录下的所有 .docx 文件（递归）"""
    folder = settings.docs_dir
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"文档目录不存在: {folder}")
    files: list[tuple[str, bytes]] = []
    for path in sorted(folder.rglob("*.docx")):
        try:
            files.append((path.name, path.read_bytes()))
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"读取文件失败 {path}: {exc}") from exc
    return files


def _reindex_documents() -> tuple[int, int]:
    """解析并向量化文件夹内全部 docx → 整体写入 pgvector，返回（文档数, 分块数）"""
    files = _read_docx_files()
    rows: list[db.DocumentChunk] = []
    for name, content in files:
        text = registry.get(name).parse(content, name)
        for idx, chunk in enumerate(split_text(text)):
            rows.append({"filename": name, "index": idx, "text": chunk, "vector": []})
    if not rows:
        db.replace_document_chunks([])
        return 0, 0
    vectors = embed_texts([row["text"] for row in rows], settings.embed_model)
    for row, vector in zip(rows, vectors, strict=True):
        row["vector"] = vector
    db.replace_document_chunks(rows)
    return len(files), len(rows)


def _reindex_quotes() -> int:
    """报价表全量向量化 → 整体写入 pgvector，返回报价数"""
    quotes = db.load_quotes()
    if not quotes:
        db.replace_quote_embeddings([])
        return 0
    vectors = embed_texts([quote["text"] for quote in quotes], settings.embed_model)
    for quote, vector in zip(quotes, vectors, strict=True):
        quote["vector"] = vector
    db.replace_quote_embeddings(quotes)
    return len(quotes)


@router.post("/reindex", response_model=ReindexResponse)
def reindex() -> ReindexResponse:
    """重索引：文件夹全部文档 + 全部报价"""
    document_count, chunk_count = _reindex_documents()
    quote_count = _reindex_quotes()
    return ReindexResponse(documents=document_count, chunks=chunk_count, quotes=quote_count)


@router.post("/reindex-quotes", response_model=ReindexResponse)
def reindex_quotes() -> ReindexResponse:
    """仅重索引报价（web 侧报价 CRUD 后调用）"""
    quote_count = _reindex_quotes()
    return ReindexResponse(documents=0, chunks=0, quotes=quote_count)


@router.get("/documents", response_model=list[DocumentItem])
def list_documents() -> list[DocumentItem]:
    """已索引文档列表（按文件名聚合分块数）"""
    return [
        DocumentItem(
            filename=item["filename"],
            chunkCount=int(item["chunk_count"]),
            updatedAt=item["updated_at"],
        )
        for item in db.list_documents()
    ]
