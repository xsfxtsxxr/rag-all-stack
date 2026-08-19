import re


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按段落切分文本；超长段落按 chunk_size 硬切并保留 overlap 重叠。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 1 > chunk_size:
            chunks.append(current)
            current = ""
        if len(para) > chunk_size:
            start = 0
            while start < len(para):
                end = min(start + chunk_size, len(para))
                chunks.append(para[start:end])
                if end >= len(para):
                    break
                start = end - overlap
            continue
        current = f"{current}\n{para}".strip() if current else para

    if current:
        chunks.append(current)
    return chunks
