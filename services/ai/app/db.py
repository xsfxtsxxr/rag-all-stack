"""pgvector 存储层：文档分块与报价向量的写入、检索（连接池 + 启动建表）。"""

from typing import TypedDict

from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings


class DocumentChunk(TypedDict):
    filename: str
    index: int
    text: str
    vector: list[float]


class QuoteVector(TypedDict):
    quote_id: str
    product_name: str
    model_no: str
    spec_summary: str
    price: str
    currency: str
    effective_date: str
    text: str
    vector: list[float]


_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """连接池单例（懒加载）"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(settings.database_url, min_size=1, max_size=4)
        _pool.wait()
    return _pool


def ensure_schema() -> None:
    """启动时确保 pgvector 扩展与表存在（幂等）"""
    dim = settings.embed_dim
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            sql.SQL(
                """
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id BIGSERIAL PRIMARY KEY,
                        filename TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        embedding vector({dim}),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
            ).format(dim=sql.Literal(dim))
        )
        cur.execute(
            sql.SQL(
                """
                    CREATE TABLE IF NOT EXISTS quote_embeddings (
                        quote_id UUID PRIMARY KEY,
                        product_name TEXT NOT NULL,
                        model_no TEXT NOT NULL,
                        spec_summary TEXT NOT NULL DEFAULT '',
                        price TEXT NOT NULL,
                        currency TEXT NOT NULL DEFAULT 'CNY',
                        effective_date TEXT NOT NULL DEFAULT '',
                        text TEXT NOT NULL,
                        embedding vector({dim})
                    )
                    """
            ).format(dim=sql.Literal(dim))
        )


def _vec_literal(vector: list[float]) -> str:
    """向量序列化为 pgvector 字面量字符串"""
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def replace_document_chunks(rows: list[DocumentChunk]) -> None:
    """清空文档分块表后整体写入（文件夹扫描式重索引）"""
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM document_chunks")
        if rows:
            cur.executemany(
                "INSERT INTO document_chunks (filename, chunk_index, text, embedding) "
                "VALUES (%s, %s, %s, %s::vector)",
                [
                    (row["filename"], row["index"], row["text"], _vec_literal(row["vector"]))
                    for row in rows
                ],
            )


def list_documents() -> list[dict[str, str]]:
    """按文件名聚合的分块统计（供管理页展示）"""
    with get_pool().connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT filename, COUNT(*) AS chunk_count, MAX(created_at) AS updated_at "
            "FROM document_chunks GROUP BY filename ORDER BY filename"
        )
        return [
            {
                "filename": str(row["filename"]),
                "chunk_count": str(row["chunk_count"]),
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else "",
            }
            for row in cur.fetchall()
        ]


def search_documents(vector: list[float], limit: int) -> list[dict[str, str]]:
    """文档分块余弦相似度检索"""
    with get_pool().connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT filename, text FROM document_chunks ORDER BY embedding <=> %s::vector LIMIT %s",
            (_vec_literal(vector), limit),
        )
        return [
            {"text": str(row["text"]), "source": str(row["filename"])} for row in cur.fetchall()
        ]


def search_quotes(vector: list[float], limit: int) -> list[dict[str, str]]:
    """报价向量余弦相似度检索"""
    with get_pool().connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT product_name, model_no, text FROM quote_embeddings "
            "ORDER BY embedding <=> %s::vector LIMIT %s",
            (_vec_literal(vector), limit),
        )
        return [
            {
                "text": str(row["text"]),
                "source": f"{row['product_name']} {row['model_no']}".strip(),
            }
            for row in cur.fetchall()
        ]


def load_quotes() -> list[QuoteVector]:
    """读取 quotes 业务表并转为待向量化的行（vector 为空，由调用方填充）"""
    with get_pool().connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, product_name, model_no, spec_summary, price, currency, effective_date "
            "FROM quotes ORDER BY created_at"
        )
        rows: list[QuoteVector] = []
        for row in cur.fetchall():
            effective = row["effective_date"].isoformat() if row["effective_date"] else ""
            text = (
                f"产品{row['product_name']} 型号{row['model_no']} "
                f"规格简述{row['spec_summary']} 价格{row['price']}{row['currency']} "
                f"有效期至{effective}"
            )
            rows.append(
                {
                    "quote_id": str(row["id"]),
                    "product_name": str(row["product_name"]),
                    "model_no": str(row["model_no"]),
                    "spec_summary": str(row["spec_summary"]),
                    "price": str(row["price"]),
                    "currency": str(row["currency"]),
                    "effective_date": effective,
                    "text": text,
                    "vector": [],
                }
            )
        return rows


def replace_quote_embeddings(rows: list[QuoteVector]) -> None:
    """清空报价向量表后整体写入"""
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM quote_embeddings")
        if rows:
            cur.executemany(
                "INSERT INTO quote_embeddings "
                "(quote_id, product_name, model_no, spec_summary, price, currency, "
                "effective_date, text, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)",
                [
                    (
                        row["quote_id"],
                        row["product_name"],
                        row["model_no"],
                        row["spec_summary"],
                        row["price"],
                        row["currency"],
                        row["effective_date"],
                        row["text"],
                        _vec_literal(row["vector"]),
                    )
                    for row in rows
                ],
            )
