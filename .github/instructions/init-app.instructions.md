---
name: init-app
description: 创建一个名为 rag-all-stack 的工业销售询盘知识库系统项目（精简版：本地文件夹文档 + 单库 pgvector），技术栈以及功能需求如下
---

你是一位资深全栈工程师，请严格按照以下要求创建一个名为 rag-all-stack 的项目。项目是一个面向工业销售询盘的知识库系统（精简版）：支持文档管理（本地文件夹扫描索引）、报价管理与智能问答。**不包含**文件上传、附件比对、消息队列与独立向量数据库，整体保持轻量。

### 前端 & 后端一体化（Next.js）

- **Next.js**: 使用创建时的最新稳定版（当前目标 16.x），初始化后执行 `pnpm audit` 确认无高危/严重漏洞，并在 `package.json` 中锁定精确版本
- **前端状态管理**: Zustand
- **前端 UI**: Tailwind CSS + shadcn/ui 组件库
- **认证**: NextAuth.js v5（若正式稳定版未发布则锁定最新 beta；如与 Next.js 版本存在兼容性问题则回退 v4，并在 README 中说明）
- **包管理器**: pnpm（monorepo 使用 Turborepo）
- **代码风格**: ESLint + Prettier + TypeScript 严格模式
- **对外业务 API**: 统一由 Next.js Route Handlers 承担（不引入独立 Node 服务）

### Python AI 服务

- **Python**: 3.13.x
- **依赖管理**: Poetry
- **框架**: FastAPI
- **文档解析**: python-docx —— 仅解析 Word（.docx），段落 + 表格单元格文本提取，不做 OCR/PDF（场景为 1-2MB 以内的小型 Word 文档）
- **文本向量化**: fastembed（ONNX Runtime 本地推理）—— 无 torch 重依赖，镜像体积小、构建快，免费开源；默认中文模型 `BAAI/bge-small-zh-v1.5`（512 维），英文场景可切换 `all-MiniLM-L6-v2`，模型名称通过环境变量配置
- **LLM**: 通过 httpx 直接调用 OpenAI 兼容接口（本地 Ollama / llama.cpp 或云端 API），流式输出；接口地址与模型名通过环境变量配置，未配置时降级为直接返回检索资料
- **向量检索**: PostgreSQL pgvector —— AI 服务负责建表（`document_chunks` / `quote_embeddings`）、写入与余弦相似度检索，不引入 Qdrant

### 数据存储

- **数据库**: PostgreSQL 16.x（`pgvector/pgvector:pg16` 镜像，含 pgvector 插件），唯一的持久化存储：业务表 + 向量表都在其中
- **文件**: 不需要对象存储。Word 文档放在宿主机本地目录（`data/inbox/`），以只读卷挂载进 AI 容器，由 AI 服务扫描解析

### 项目结构（必须遵循）

目录分层约定：`apps/` 放可运行应用，`packages/` 放共享库，`tooling/` 放共享工程配置（参考 Turborepo 官方模板），`services/` 放非 Node 服务（Poetry 独立管理，**不加入 pnpm 工作区**）。对外业务 API 统一由 Next.js Route Handlers 承担。

```
rag-all-stack/
├── pnpm-workspace.yaml          # 工作区：apps/* packages/* tooling/*（services/ 不加入）
├── package.json                 # 根 package.json（Turborepo + 共享 devDependencies）
├── turbo.json                   # Turborepo pipeline 配置
├── .gitignore
├── .editorconfig
├── .env.example                 # 应用共用环境文件（复制为 .env；compose 不用它）
├── .github/
│   ├── instructions/            # AI 编码规范（init-app / nodejs-24 / python-313）
│   └── workflows/
│       └── ci.yml               # CI：lint + typecheck + test
├── .vscode/
│   └── settings.json            # 编辑器统一配置（Python strict 等）
├── docker-compose/              # 基础设施编排（环境变量从同目录 .env 读取）
│   ├── docker-compose.yml       # PostgreSQL + AI 服务（仅两个服务）
│   └── .env.example             # compose 专用环境变量（复制为 .env）
├── data/
│   └── inbox/                   # 待索引 Word 文档目录（挂载进 AI 容器，只读）
│       └── .gitkeep
├── docs/                        # 产品规格说明书与项目文档（纯资料，不含可运行代码）
│   └── .gitkeep
├── apps/
│   └── web/                     # Next.js 应用（App Router）
│       ├── app/
│       │   ├── layout.tsx       # 根布局
│       │   ├── globals.css      # Tailwind 入口样式
│       │   ├── page.tsx         # 主询盘页面（聊天输入框）
│       │   ├── login/
│       │   │   └── page.tsx     # NextAuth 登录页
│       │   ├── admin/
│       │   │   ├── quotes/      # 报价管理 CRUD 页面
│       │   │   └── documents/   # 文档管理页面（扫描索引 + 已索引列表）
│       │   └── api/
│       │       ├── auth/[...nextauth]/route.ts # NextAuth 认证
│       │       ├── ask/route.ts              # 问答接口（SSE 流式代理）
│       │       ├── quotes/route.ts           # 报价 CRUD 接口
│       │       ├── quotes/[id]/route.ts      # 报价单个资源接口
│       │       └── sync/route.ts             # 触发全量重索引（转发 AI 服务）
│       ├── components/
│       │   ├── ui/              # shadcn/ui 生成的组件
│       │   ├── chat/            # 聊天组件
│       │   └── admin/           # 管理页交互组件（重索引按钮）
│       ├── lib/
│       │   ├── auth.ts          # NextAuth 配置
│       │   ├── ai.ts            # AI 服务地址与报价索引刷新
│       │   ├── db.ts            # Drizzle 数据库连接
│       │   └── utils.ts         # 类名合并工具
│       ├── proxy.ts             # Next 16 会话保护（替代 middleware）
│       ├── next.config.ts
│       ├── postcss.config.mjs
│       ├── tsconfig.json
│       └── package.json
├── packages/
│   ├── database/                # Drizzle schema + migrations（web 与脚本共享）
│   │   ├── schema/
│   │   │   └── quotes.ts
│   │   ├── migrations/          # Drizzle 生成的迁移 SQL
│   │   ├── seeds/               # 种子脚本（示例报价）
│   │   ├── drizzle.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   └── shared-types/            # 跨端共享 TypeScript 类型
│       ├── src/
│       │   └── index.ts         # 统一导出入口
│       ├── tsconfig.json
│       └── package.json
├── tooling/                     # 共享工程配置（每个包内含 package.json）
│   ├── typescript-config/       # base.json / nextjs.json / node.json
│   ├── eslint-config/           # 统一 ESLint Flat Config
│   └── prettier-config/         # 统一 Prettier 配置
├── services/
│   └── ai/                      # FastAPI AI 服务（Poetry 管理，非 pnpm 工作区）
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── config.py        # pydantic-settings 配置
│       │   ├── db.py            # pgvector 建表/写入/检索（psycopg 连接池）
│       │   ├── routers/         # API 路由（问答 / 索引）
│       │   ├── parsers/         # 文档解析（docx）
│       │   ├── embeddings/      # 文本向量化（fastembed）
│       │   └── rag/             # 问答链（httpx 流式 LLM）
│       ├── tests/               # pytest 单测（镜像 app/ 结构）
│       ├── .dockerignore
│       ├── pyproject.toml       # Poetry 配置
│       ├── poetry.lock
│       └── Dockerfile
└── README.md
```

### 功能需求（代码中必须体现）

1. **文档扫描索引**
   - 用户把 Word（.docx）文档放入 `data/inbox/` 目录（通过只读卷挂载到 AI 容器 `/data/inbox`）。
   - 管理页（`/admin/documents`）提供「扫描文件夹并重建索引」按钮，调用 `/api/sync` → AI 服务 `/api/reindex`。
   - AI 服务扫描目录下全部 .docx，python-docx 提取文本、分块（chunk size 500、overlap 50）、fastembed 向量化，整体写入 PostgreSQL 的 `document_chunks` 表（含 pgvector `embedding` 列）。
   - 文档列表页展示已索引文档（文件名、分块数、索引时间），数据来自 AI 服务 `/api/documents`。

2. **报价管理**
   - 数据库表 `quotes` 包含字段：id, product_name, model_no, spec_summary, price, currency, effective_date, status。
   - 管理后台提供 CRUD 表格，支持增删改查。
   - 报价变更（INSERT/UPDATE/DELETE）后，web 侧 fire-and-forget 调用 AI 服务 `/api/reindex-quotes`，AI 服务全量重嵌入 `quotes` 表并整体写入 `quote_embeddings` 表（报价量小，全量重建成本可忽略）。

3. **智能问答**
   - 主页面提供类似 ChatGPT 的聊天输入框，用户输入问题后，调用 `/api/ask`（SSE 流式代理）。
   - AI 服务收到问题后：fastembed 向量化 → pgvector 从 `document_chunks` 与 `quote_embeddings` 各检索 top-5 → 合并上下文 → 可选调用 OpenAI 兼容 LLM 生成回答。
   - LLM 返回的回答需包含引用的产品型号和报价，并注明价格有效期；未配置 LLM 时降级为直接返回检索资料。
   - 支持流式输出（SSE：`data: {...}\n\n` 事件流，以 `data: [DONE]` 结束）。

4. **开发环境**
   - 提供 `docker-compose/docker-compose.yml`：默认只启动 PostgreSQL（`pgvector/pgvector:pg16`）；AI 服务（`services/ai/Dockerfile` 构建，挂载 `../data/inbox` 只读卷）挂在 `deploy` profile 下，部署时用 `--profile deploy` 启动。本地开发 AI 服务在宿主机直跑（`poetry run uvicorn app.main:app --reload --port 8008`，读取根 `.env`）。
   - Next.js 在宿主机运行（热更新方便）。
   - 环境文件只有两份：根 `.env`（模板 `.env.example`）给应用共用（Next.js 在 `next.config.ts` 显式加载；数据库脚本用 `tsx --env-file` 加载；AI 服务用 pydantic-settings 指向根 `.env`）；`docker-compose/.env`（模板 `docker-compose/.env.example`）专放 compose 变量（镜像、宿主机端口、凭据），compose 自动加载同目录 `.env`。不再为各应用单独维护 `.env.example`。

### 代码质量要求

- `.github/instructions/` 下已提供 `nodejs-24`（适用于 `**/*.ts`）与 `python-313`（适用于 `**/*.py`）两份语言规范，所有 TS/Python 代码必须遵守其中的依赖管理、格式化、类型标注与测试约定。
- 使用 TypeScript 严格模式，所有函数必须有类型注解。
- 遵循 ESLint + Prettier 配置。
- 关键业务逻辑（如检索、索引）添加注释说明。
- 提供 `README.md` 包含项目简介、启动步骤、环境变量说明。

请先生成完整的项目文件树，然后逐一创建每个文件的内容。确保所有代码可运行，依赖版本正确。
