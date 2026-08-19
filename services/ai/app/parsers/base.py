from abc import ABC, abstractmethod


class DocumentParser(ABC):
    """文档解析器基类：按扩展名路由，输入字节流，输出纯文本"""

    @abstractmethod
    def supports(self, filename: str) -> bool: ...

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> str: ...


class ParserRegistry:
    """解析器注册表（按扩展名选择解析器）"""

    def __init__(self) -> None:
        self._parsers: list[DocumentParser] = []

    def register(self, parser: DocumentParser) -> None:
        self._parsers.append(parser)

    def get(self, filename: str) -> DocumentParser:
        for parser in self._parsers:
            if parser.supports(filename):
                return parser
        raise ValueError(f"不支持的文件类型: {filename}")
