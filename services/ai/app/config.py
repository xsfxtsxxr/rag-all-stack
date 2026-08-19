from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_env_file() -> Path:
    """仓库根目录 .env（services/ai/app/config.py 向上 4 级）。

    Docker 容器内路径为 /srv/app/config.py，向上不足 4 级，
    此时停在文件系统根，/.env 不存在会被 pydantic-settings 静默忽略。
    """
    path = Path(__file__).resolve()
    for _ in range(4):
        if path.parent == path:
            break
        path = path.parent
    return path / ".env"


ENV_FILE = _repo_env_file()


class Settings(BaseSettings):
    """AI 服务配置（读取根目录 .env 或环境变量）"""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    embed_model: str = "BAAI/bge-small-zh-v1.5"
    embed_dim: int = 512
    database_url: str = (
        "postgres://rag_all_stack_db:rag_all_stack_db@localhost:55432/rag_all_stack_db"
    )
    docs_dir: Path = Path("/data/inbox")
    llm_base_url: str | None = None
    llm_model: str = "qwen2.5"
    llm_api_key: str | None = None
    # 推理强度 low/high/max（glm-5.3 等推理模型）；None 表示不发送该参数
    llm_reasoning_effort: str | None = None
    # 嵌入模型下载源（本地直跑时由 embeddings 模块写入 HF_ENDPOINT 环境变量）
    hf_endpoint: str = "https://hf-mirror.com"


settings = Settings()
