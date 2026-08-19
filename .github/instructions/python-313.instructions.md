---
description: "编写或修改 Python 代码、管理依赖（poetry）、格式化与静态检查（Ruff）、类型标注（Pylance standard + mypy）、编写测试（pytest）。适用于所有 .py 文件。"
applyTo: "**/*.py"
---

## 1. 环境与工具链

- 目标解释器：**Python 3.13.x**，依赖管理用 **poetry**（`pyproject.toml` + `poetry.lock`）。
- 新增依赖：运行时 `poetry add <pkg>`；开发依赖 `poetry add --group dev <pkg>`。**禁止**手写 `requirements.txt`、混用 `pip install` / `conda install` 装业务依赖。
- 虚拟环境由 Poetry 统一管理：在项目根执行 `poetry install`，启用项目内 `.venv`（`poetry config virtualenvs.in-project true` 或 `poetry.toml`）；VS Code 的解释器必须选择该 `.venv/bin/python`。
- 终端执行命令一律通过 `poetry run <cmd>`（如 `poetry run ruff check .`），禁止手动 `python -m venv` 或切到其他解释器。
- 全部工具配置（Ruff / mypy / pytest）集中在 `pyproject.toml`，不散落 `.cfg`/`.ini`。
- 格式化与 lint 由 **Ruff** 承担（`ruff format` + `ruff check`），不再引入 Black/isort/flake8。
- `poetry.lock` 必须提交。

## 2. 代码风格（Ruff）

- `[tool.ruff]` 建议：`line-length = 100`，`target-version = "py313"`，启用 `E, F, I, UP, B, SIM, TID` 规则集。
- 提交前必须 `poetry run ruff format --check .` 与 `poetry run ruff check .` 通过。

## 3. 类型标注（Pylance + mypy）

- 所有函数必须显式标注参数与返回值类型；禁止裸 `Any`（可用 `object`、泛型、`Protocol`、`TypedDict` 替代）。
- `[tool.mypy]` 开启 `strict = true`；确需放宽处用精确的 `# type: ignore[<code>]` 并注明原因。
- 工作区 `.vscode/settings.json` 设置 `"python.analysis.typeCheckingMode": "strict"`，使 Pylance 与 mypy 保持一致。
- 数据模型用 Pydantic v2（`Field` 校验、`model_config`），禁止手写 JSON 解析与字段拼装。

## 4. 测试（pytest）

- 统一 pytest（`[tool.pytest.ini_options]` 配置），测试文件命名 `test_*.py`，放在 `tests/` 下镜像 `app/` 结构。
- 解析器、分块、嵌入、RAG 链等核心逻辑必须有单测；禁止在测试中访问真实 Qdrant/PostgreSQL/外部模型，使用 mock 或固定样本。
- 运行：`poetry run pytest`；CI 中同时执行 `ruff check` 与 `mypy`。

## 5. FastAPI 约定

- 路由放在 `app/routers/`，用 `APIRouter` 组织；请求/响应体全部用 Pydantic v2 模型。
- I/O 相关 handler 用 `async def`；CPU 密集（文档解析、嵌入推理）用 `def`（FastAPI 自动放入线程池），避免阻塞事件循环。
- 模型（嵌入/LLM）懒加载：全局单例 + 首次调用时初始化，避免启动时长时间阻塞。
- 统一异常处理与结构化日志；接口错误返回 HTTP 语义化状态码，不自定义包装层。
