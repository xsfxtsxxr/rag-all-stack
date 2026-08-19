from app.parsers.base import ParserRegistry
from app.parsers.docx import DocxParser

registry = ParserRegistry()
registry.register(DocxParser())

__all__ = ["registry"]
