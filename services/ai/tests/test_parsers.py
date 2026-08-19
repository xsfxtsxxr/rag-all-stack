from io import BytesIO

import pytest
from docx import Document

from app.parsers import registry


def test_registry_supports_docx() -> None:
    assert registry.get("合同.docx").supports("合同.docx")


def test_registry_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        registry.get("笔记.txt")


def test_docx_parse_paragraphs_and_tables() -> None:
    doc = Document()
    doc.add_paragraph("第一条：产品规格")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "型号"
    table.rows[0].cells[1].text = "VFD-220"
    buf = BytesIO()
    doc.save(buf)

    text = registry.get("报价单.docx").parse(buf.getvalue(), "报价单.docx")
    assert "产品规格" in text
    assert "VFD-220" in text
