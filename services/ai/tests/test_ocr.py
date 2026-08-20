"""OCR 模块测试（mock 引擎，不加载真实模型、不访问网络）。"""

import pytest
from rapidocr.utils.output import RapidOCROutput

from app import ocr


def test_ocr_joins_lines_and_skips_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_engine(content: bytes) -> RapidOCROutput:
        del content
        # RapidOCROutput.txts 注解为定长 Tuple[str]，运行时接受任意长度元组
        return RapidOCROutput(txts=("额定电压 380V", "   ", "功率 5.5kW"))  # type: ignore[arg-type]

    monkeypatch.setattr(ocr, "_get_engine", lambda: fake_engine)
    assert ocr.ocr_image(b"fake-image-bytes") == "额定电压 380V\n功率 5.5kW"


def test_ocr_empty_result_returns_empty_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_engine(content: bytes) -> RapidOCROutput:
        del content
        return RapidOCROutput(txts=None)

    monkeypatch.setattr(ocr, "_get_engine", lambda: fake_engine)
    assert ocr.ocr_image(b"blank-image") == ""


def test_ocr_engine_error_wrapped_as_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_engine(content: bytes) -> RapidOCROutput:
        del content
        raise RuntimeError("invalid image bytes")

    monkeypatch.setattr(ocr, "_get_engine", lambda: fake_engine)
    with pytest.raises(ValueError, match="图片解码或识别失败"):
        ocr.ocr_image(b"not-an-image")
