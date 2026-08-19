import { AskRequestSchema } from '@rag/shared-types'
import type { NextRequest } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * 问答接口（SSE 流式代理）：
 * 向量检索 + LLM 生成全部由 AI 服务完成，web 只做参数校验与流式转发。
 */
export async function POST(req: NextRequest) {
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
    const aiUrl = `${process.env.AI_SERVICE_URL ?? 'http://localhost:8008'}/api/ask/stream`
    const upstream = await fetch(aiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: parsed.data.question }),
    })
    if (!upstream.ok || !upstream.body) {
      return Response.json({ error: `AI 服务返回 ${upstream.status}` }, { status: 502 })
    }

    return new Response(upstream.body, {
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    })
  } catch (e) {
    return Response.json(
      { error: e instanceof Error ? e.message : '问答服务异常' },
      { status: 500 },
    )
  }
}
