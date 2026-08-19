import pytest

from app.parsers.chunker import split_text


def test_split_short_paragraphs() -> None:
    chunks = split_text("第一段。\n\n第二段。", chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert "第一段" in chunks[0]
    assert "第二段" in chunks[0]


def test_split_long_paragraph_with_overlap() -> None:
    text = "字" * 1200
    chunks = split_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 3
    assert all(len(chunk) <= 500 for chunk in chunks)
    # overlap 保留：后一块前 50 字 == 前一块后 50 字
    assert chunks[1][:50] == chunks[0][-50:]


def test_invalid_args() -> None:
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=100, overlap=100)
