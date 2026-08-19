import { refreshQuoteIndex } from '@/lib/ai'
import { db } from '@/lib/db'
import { quotes } from '@rag/database/schema'
import { QuoteUpsertSchema } from '@rag/shared-types'
import { eq } from 'drizzle-orm'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

type RouteContext = { params: Promise<{ id: string }> }

export async function GET(_req: Request, context: RouteContext) {
  const { id } = await context.params
  const [row] = await db.select().from(quotes).where(eq(quotes.id, id))
  if (!row) return Response.json({ error: '未找到该报价' }, { status: 404 })
  return Response.json(row)
}

export async function PUT(req: Request, context: RouteContext) {
  const { id } = await context.params
  const parsed = QuoteUpsertSchema.safeParse(await req.json())
  if (!parsed.success) {
    return Response.json({ error: parsed.error.issues[0]?.message ?? '参数错误' }, { status: 400 })
  }
  const [row] = await db.update(quotes).set(parsed.data).where(eq(quotes.id, id)).returning()
  if (!row) return Response.json({ error: '未找到该报价' }, { status: 404 })
  refreshQuoteIndex()
  return Response.json(row)
}

export async function DELETE(_req: Request, context: RouteContext) {
  const { id } = await context.params
  const [row] = await db.delete(quotes).where(eq(quotes.id, id)).returning()
  if (!row) return Response.json({ error: '未找到该报价' }, { status: 404 })
  refreshQuoteIndex()
  return new Response(null, { status: 204 })
}
