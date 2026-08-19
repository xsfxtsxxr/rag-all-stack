import { refreshQuoteIndex } from '@/lib/ai'
import { db } from '@/lib/db'
import { quotes } from '@rag/database/schema'
import { QuoteUpsertSchema } from '@rag/shared-types'
import { desc } from 'drizzle-orm'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * 报价 CRUD。
 * 变更后由 AI 服务重建报价向量索引（fire-and-forget，失败不阻塞写入）。
 */
export async function GET() {
  const rows = await db.select().from(quotes).orderBy(desc(quotes.createdAt))
  return Response.json(rows)
}

export async function POST(req: Request) {
  const parsed = QuoteUpsertSchema.safeParse(await req.json())
  if (!parsed.success) {
    return Response.json({ error: parsed.error.issues[0]?.message ?? '参数错误' }, { status: 400 })
  }
  const [row] = await db.insert(quotes).values(parsed.data).returning()
  refreshQuoteIndex()
  return Response.json(row, { status: 201 })
}
