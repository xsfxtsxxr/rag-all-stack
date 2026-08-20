import { AskRequestSchema } from '@rag/shared-types'
import type { NextRequest } from 'next/server'
import { z } from 'zod'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ALLOWED_IMAGE_TYPES: readonly string[] = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/bmp',
]

function aiServiceUrl(): string {
  return process.env.AI_SERVICE_URL ?? 'http://localhost:8008'
}

/** 上游 SSE 流统一转发（透传事件流响应头） */
function streamResponse(upstream: Response): Response {
  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}

/** 图片询盘：校验 multipart 表单（question + image）后转发给 AI 服务 /api/ask/image */
async function handleImageAsk(req: NextRequest): Promise<Response> {
  let form: FormData
  try {
    form = await req.formData()
  } catch {
    return Response.json({ error: '请求体不是合法的 multipart 表单' }, { status: 400 })
  }
  const questionValue = form.get('question')
  const question = typeof questionValue === 'string' ? questionValue : ''
  const parsed = z.string().min(1).max(2000).safeParse(question)
  if (!parsed.success) {
    return Response.json({ error: parsed.error.issues[0]?.message ?? '参数错误' }, { status: 400 })
  }
  const file = form.get('image')
  if (!(file instanceof File) || file.size === 0) {
    return Response.json({ error: '缺少图片文件' }, { status: 400 })
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return Response.json({ error: '图片大小不能超过 5MB' }, { status: 400 })
  }
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return Response.json({ error: '仅支持 jpg/png/webp/bmp 格式图片' }, { status: 400 })
  }

  try {
    const upstreamForm = new FormData()
    upstreamForm.append('question', parsed.data)
    upstreamForm.append('image', file)
    const upstream = await fetch(`${aiServiceUrl()}/api/ask/image`, {
      method: 'POST',
      body: upstreamForm,
    })
    if (!upstream.ok || !upstream.body) {
      return Response.json({ error: `AI 服务返回 ${upstream.status}` }, { status: 502 })
    }
    return streamResponse(upstream)
  } catch (e) {
    return Response.json(
      { error: e instanceof Error ? e.message : '问答服务异常' },
      { status: 500 },
    )
  }
}

/**
 * 问答接口（SSE 流式代理）：
 * - JSON：纯文本提问，转发 AI 服务 /api/ask/stream
 * - multipart：携带规格参数截图，转发 AI 服务 /api/ask/image（OCR + 检索 + 生成）
 */
export async function POST(req: NextRequest): Promise<Response> {
  const contentType = req.headers.get('content-type') ?? ''
  if (contentType.includes('multipart/form-data')) {
    return handleImageAsk(req)
  }

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return Response.json({ error: '请求体不是合法 JSON' }, { status: 400 })
  }
  const parsed = AskRequestSchema.safeParse(body)
  if (!parsed.success) {
    return Response.json({ error: parsed.error.issues[0]?.message ?? '参数错误' }, { status: 400 })
  }

  try {
    const aiUrl = `${aiServiceUrl()}/api/ask/stream`
    const upstream = await fetch(aiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: parsed.data.question }),
    })
    if (!upstream.ok || !upstream.body) {
      return Response.json({ error: `AI 服务返回 ${upstream.status}` }, { status: 502 })
    }
    return streamResponse(upstream)
  } catch (e) {
    return Response.json(
      { error: e instanceof Error ? e.message : '问答服务异常' },
      { status: 500 },
    )
  }
}
