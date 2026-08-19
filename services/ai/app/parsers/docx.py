from io import BytesIO

from docx import Document

from app.parsers.base import DocumentParser


class DocxParser(DocumentParser):
    """Word 文档解析（python-docx）：段落 + 表格单元格文本"""

    def supports(self, filename: str) -> bool:
        return filename.lower().endswith(".docx")

    def parse(self, content: bytes, filename: str) -> str:
        del filename  # 保留接口一致性
        doc = Document(BytesIO(content))
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
