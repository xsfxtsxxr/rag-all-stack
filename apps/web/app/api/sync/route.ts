import { aiUrl } from '@/lib/ai'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/** 手动触发全量重索引：AI 服务扫描文档文件夹并重建 pgvector 索引 */
export async function POST() {
  const res = await fetch(`${aiUrl()}/api/reindex`, { method: 'POST' })
  if (!res.ok) {
    return Response.json({ error: `AI 服务返回 ${res.status}` }, { status: 502 })
  }
  return Response.json(await res.json())
}
