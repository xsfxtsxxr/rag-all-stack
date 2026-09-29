# rag-all-stack API 接口文档

工业销售询盘知识库系统（精简版）对外暴露两类接口：

1. **业务 API**：由 Next.js Route Handlers 承担（`apps/web/app/api/**`），面向前端页面调用。
2. **AI 服务 API**：由 FastAPI 服务承担（`services/ai/app/routers/**`），负责文档索引、向量检索与问答生成，默认监听 `http://localhost:8008`。

> 约定：除注明外，请求/响应均使用 `application/json`；流式接口使用 `text/event-stream`（SSE）。

---

## 目录

- [一、业务 API（Next.js）](#一业务-apinextjs)
  - [1. 问答 `/api/ask`](#1-问答-apiask)
  - [2. 报价列表/新建 `/api/quotes`](#2-报价列表新建-apiquotes)
  - [3. 报价单资源 `/api/quotes/[id]`](#3-报价单资源-apiquotesid)
  - [4. 触发全量重索引 `/api/sync`](#4-触发全量重索引-apisync)
  - [5. 认证 `/api/auth/[...nextauth]`](#5-认证-apiauthnextauth)
- [二、AI 服务 API（FastAPI）](#二ai-服务-apifastapi)
  - [1. 健康检查 `/healthz`](#1-健康检查-healthz)
  - [2. 流式问答 `/api/ask/stream`](#2-流式问答-apiaskstream)
  - [3. 图片询盘 `/api/ask/image`](#3-图片询盘-apiaskimage)
  - [4. 全量重索引 `/api/reindex`](#4-全量重索引-apireindex)
  - [5. 重索引报价 `/api/reindex-quotes`](#5-重索引报价-apireindex-quotes)
  - [6. 已索引文档列表 `/api/documents`](#6-已索引文档列表-apidocuments)
- [三、SSE 事件流格式](#三sse-事件流格式)
- [四、通用错误格式](#四通用错误格式)

---

## 一、业务 API（Next.js）

### 1. 问答 `/api/ask`

主询盘页聊天框的问答入口，SSE 流式代理到 AI 服务。根据 `Content-Type` 区分两种模式。

**`POST /api/ask`（纯文本提问）**

- 请求头：`Content-Type: application/json`
- 请求体：

| 字段       | 类型   | 必填 | 说明                                                                            |
| ---------- | ------ | ---- | ------------------------------------------------------------------------------- |
| `question` | string | 是   | 用户问题，长度 1–2000                                                           |
| `history`  | array  | 否   | 历史对话，最多 10 条，元素为 `{ role: 'user' \| 'assistant', content: string }` |

```json
{
  "question": "你们有没有用于过电压监测的产品？",
  "history": []
}
```

- 响应：`200`，`text/event-stream`，逐 token 输出（格式见 [SSE 事件流](#三sse-事件流格式)）。
- 校验失败返回 `400`；上游 AI 服务异常返回 `502`；内部异常返回 `500`。

**`POST /api/ask`（图片询盘）**

- 请求头：`Content-Type: multipart/form-data`
- 表单字段：

| 字段       | 类型   | 必填 | 说明                                                  |
| ---------- | ------ | ---- | ----------------------------------------------------- |
| `question` | string | 否   | 用户问题，长度 1–2000（缺省时由 AI 服务使用默认提示） |
| `image`    | file   | 是   | 技术规格参数截图，`jpg/png/webp/bmp`，≤ 5MB           |

- 响应：`200`，`text/event-stream`。
- 错误：表单非法 `400`、缺少图片 `400`、图片超限/格式不支持 `400`、AI 服务异常 `502`。

### 2. 报价列表/新建 `/api/quotes`

**`GET /api/quotes`**

返回全部报价，按创建时间倒序。

- 响应 `200`：

```json
[
  {
    "id": "f1a2b3c4-...",
    "productName": "红外窗口（磁吸式）",
    "modelNo": "ZP-HW-M",
    "specSummary": "磁吸式安装，适用柜体开孔 100mm",
    "price": "1280.00",
    "currency": "CNY",
    "effectiveDate": "2026-09-29",
    "status": "active",
    "createdAt": "2026-09-29T08:00:00.000Z",
    "updatedAt": "2026-09-29T08:00:00.000Z"
  }
]
```

**`POST /api/quotes`**

新建报价，成功后异步（fire-and-forget）通知 AI 服务重建报价向量索引。

- 请求体：

| 字段            | 类型   | 必填 | 说明                                           |
| --------------- | ------ | ---- | ---------------------------------------------- |
| `productName`   | string | 是   | 产品名称，1–200 字符                           |
| `modelNo`       | string | 是   | 产品型号，1–100 字符                           |
| `specSummary`   | string | 否   | 规格摘要，≤2000 字符，默认 `""`                |
| `price`         | string | 是   | 价格，数字（最多两位小数）                     |
| `currency`      | string | 否   | 货币代码，3 位，默认 `CNY`                     |
| `effectiveDate` | date   | 是   | 价格有效期（`YYYY-MM-DD`）                     |
| `status`        | enum   | 否   | `active` / `inactive` / `draft`，默认 `active` |

```json
{
  "productName": "红外窗口（磁吸式）",
  "modelNo": "ZP-HW-M",
  "specSummary": "磁吸式安装",
  "price": "1280.00",
  "currency": "CNY",
  "effectiveDate": "2026-09-29",
  "status": "active"
}
```

- 响应：`201`，返回新建的报价资源（结构同上）；参数校验失败 `400`。

### 3. 报价单资源 `/api/quotes/[id]`

`id` 为报价 UUID。变更成功后同样会异步刷新报价向量索引。

| 方法     | 说明                       | 成功响应           | 失败响应                      |
| -------- | -------------------------- | ------------------ | ----------------------------- |
| `GET`    | 查询单个报价               | `200` 报价资源     | `404` 未找到                  |
| `PUT`    | 整体更新报价（字段同新建） | `200` 更新后的报价 | `400` 参数错误 / `404` 未找到 |
| `DELETE` | 删除报价                   | `204` 无内容       | `404` 未找到                  |

### 4. 触发全量重索引 `/api/sync`

管理页「扫描文件夹并重建索引」按钮调用，转发到 AI 服务 `/api/reindex`。

**`POST /api/sync`**

- 请求体：无。
- 响应 `200`：

```json
{
  "documents": 3,
  "chunks": 42,
  "quotes": 10
}
```

- 上游异常返回 `502`。

### 5. 认证 `/api/auth/[...nextauth]`

NextAuth v5 标准端点，由 `next-auth` 库自动接管，提供 `GET`/`POST`（如 `signin`、`callback`、`session`、`signout` 等子路径）。前端登录页使用邮箱 + 密码（Credentials 演示实现，生产需接入真实用户表）。

---

## 二、AI 服务 API（FastAPI）

基础地址：`AI_SERVICE_URL`（默认 `http://localhost:8008`）。以下路径均已含 `/api` 前缀（由 router 定义）。

### 1. 健康检查 `/healthz`

**`GET /healthz`**

- 响应 `200`：`{ "status": "ok" }`

### 2. 流式问答 `/api/ask/stream`

**`POST /api/ask/stream`**

问题向量化 → pgvector 检索文档分块与报价各 top-5 → 调用 LLM 生成（未配置 LLM 时降级为直接返回检索资料）。

- 请求体：`{ "question": string }`（1–2000 字符）。
- 响应：`200`，`text/event-stream`（格式见 [SSE 事件流](#三sse-事件流格式)）。
- 向量化/检索失败返回 `500`。

### 3. 图片询盘 `/api/ask/image`

**`POST /api/ask/image`**

OCR 提取规格参数 → 向量检索 → 流式生成产品型号与价格推荐。

- 请求头：`Content-Type: multipart/form-data`
- 表单字段：

| 字段       | 类型   | 必填 | 说明                                                      |
| ---------- | ------ | ---- | --------------------------------------------------------- |
| `image`    | file   | 是   | 技术规格参数截图，`jpg/png/webp/bmp`，≤ 5MB               |
| `question` | string | 否   | 默认「这是技术规格参数截图，请帮忙分析是否有匹配的产品…」 |

- 响应：`200`，`text/event-stream`。
- 错误：格式不支持 `400`、超限 `400`、OCR 失败/未识别文字 `400`。

### 4. 全量重索引 `/api/reindex`

**`POST /api/reindex`**

扫描文档目录全部 `.docx`，解析、分块、向量化后整体写入 `document_chunks`；同时对 `quotes` 全量重嵌入写入 `quote_embeddings`。

- 请求体：无。
- 响应 `200`：

```json
{ "documents": 3, "chunks": 42, "quotes": 10 }
```

- 文档目录不存在返回 `400`；读取文件失败 `500`。

### 5. 重索引报价 `/api/reindex-quotes`

**`POST /api/reindex-quotes`**

仅对报价表全量重嵌入（web 侧报价 CRUD 后触发）。

- 响应 `200`：`{ "documents": 0, "chunks": 0, "quotes": 10 }`

### 6. 已索引文档列表 `/api/documents`

**`GET /api/documents`**

返回已索引文档列表（按文件名聚合分块数）。

- 响应 `200`：

```json
[
  {
    "filename": "中沛ZDPTL 流敏消谐电阻器.docx",
    "chunkCount": 12,
    "updatedAt": "2026-09-29T08:00:00.000Z"
  }
]
```

---

## 三、SSE 事件流格式

所有问答接口返回 `text/event-stream`，每个 token 一个 `data` 事件，以 `[DONE]` 结束：

```
data: {"token": "您"}
data: {"token": "好"}

data: {"token": "，"}

data: [DONE]
```

- 事件内容：`{"token": string}`，客户端按顺序拼接 `token` 即为完整回答。
- 结束标记：`data: [DONE]`。

未配置 `LLM_BASE_URL` 或 LLM 调用失败时，回答内容降级为「提示语 + 检索到的知识库资料文本」，同样通过上述 token 流返回。

---

## 四、通用错误格式

非流式接口出错时统一返回 JSON：

```json
{ "error": "错误描述" }
```

常见状态码：

| 状态码 | 含义                         |
| ------ | ---------------------------- |
| `400`  | 参数校验失败 / 请求体非法    |
| `401`  | 未认证（NextAuth 保护页面）  |
| `404`  | 资源不存在                   |
| `500`  | 服务内部异常                 |
| `502`  | 上游 AI 服务异常（网关错误） |
