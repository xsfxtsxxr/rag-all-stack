FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

# opencv-python（rapidocr 依赖）在 slim 镜像上需要以下系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# 可选 PyPI 镜像（网络受限环境通过 compose 的 PYPI_INDEX_URL 切换，如阿里云/清华源）
ARG PYPI_INDEX_URL=https://pypi.org/simple

# --mount=type=cache 让重试构建复用已下载的 wheel，网络抖动时不必从头下载
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --index-url "${PYPI_INDEX_URL}" poetry==2.4.1

WORKDIR /srv

# 先装依赖以利用 Docker 层缓存（poetry.lock 不存在时自动解析）
# 网络抖动时：单线程下载 + 失败重试（缓存挂载保留已下载 wheel，重试只需补齐缺失项）
COPY pyproject.toml poetry.lock* ./
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry config repositories.pypi.url "${PYPI_INDEX_URL}" && \
    poetry config installer.max-workers 1 && \
    for i in 1 2 3 4 5 6 7 8; do \
    poetry install --no-root --only main && exit 0; \
    echo "poetry install 第 ${i} 次尝试失败，5 秒后重试…"; sleep 5; \
    done; \
    exit 1

COPY app ./app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
