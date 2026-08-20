"""图片 OCR：RapidOCR（onnxruntime 引擎，默认模型打包在 wheel 内，无需联网下载）。"""

import threading

from rapidocr import RapidOCR
from rapidocr.utils.output import RapidOCROutput

_engine: RapidOCR | None = None
_lock = threading.Lock()


def _get_engine() -> RapidOCR:
    """懒加载全局单例（模型加载较慢，进程内仅初始化一次）"""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = RapidOCR()
    return _engine


def ocr_image(content: bytes) -> str:
    """图片字节流 → OCR 纯文本（按行拼接，无有效文字时返回空字符串）"""
    try:
        result = _get_engine()(content)
    except Exception as exc:
        raise ValueError(f"图片解码或识别失败: {exc}") from exc
    # 默认配置（检测+分类+识别）返回 RapidOCROutput；其他阶段组合无文本，视为无结果
    if not isinstance(result, RapidOCROutput) or result.txts is None:
        return ""
    return "\n".join(text.strip() for text in result.txts if text.strip())
