import os
import threading

from app.config import settings

# fastembed 底层依赖 huggingface_hub，后者在 import 时读取 HF_ENDPOINT，
# 因此必须在 import fastembed 之前把 .env 里的镜像源写入环境变量。
# （容器内由 compose 注入相同变量，setdefault 不会覆盖。）
os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
# 禁用 Xet 存储（镜像源不支持 cas-server 时避免 401，回退普通文件下载）
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from fastembed import TextEmbedding  # noqa: E402

_model: TextEmbedding | None = None
_lock = threading.Lock()


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    """批量文本向量化（fastembed/ONNX 本地推理，模型懒加载 + 线程安全单例）"""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = TextEmbedding(model_name=model_name)
    if _model is None:
        raise RuntimeError("嵌入模型加载失败")
    return [vec.tolist() for vec in _model.embed(texts)]
