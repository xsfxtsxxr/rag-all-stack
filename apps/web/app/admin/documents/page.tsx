import { ReindexButton } from '@/components/admin/reindex-button'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatBeijingTime } from '@/lib/utils'
import Link from 'next/link'
import { z } from 'zod'

export const dynamic = 'force-dynamic'

const DocumentsResponseSchema = z.array(
  z.object({
    filename: z.string(),
    chunkCount: z.number().int(),
    updatedAt: z.string(),
  }),
)

interface LoadResult {
  docs: { filename: string; chunkCount: number; updatedAt: string }[]
  error: string | null
}

async function loadDocuments(): Promise<LoadResult> {
  try {
    const res = await fetch(
      `${process.env.AI_SERVICE_URL ?? 'http://localhost:8008'}/api/documents`,
      { cache: 'no-store' },
    )
    if (!res.ok) throw new Error(`AI 服务返回 ${res.status}`)
    const parsed = DocumentsResponseSchema.safeParse(await res.json())
    if (!parsed.success) throw new Error('AI 服务返回格式异常')
    return { docs: parsed.data, error: null }
  } catch (e) {
    return { docs: [], error: e instanceof Error ? e.message : '无法连接 AI 服务' }
  }
}

export default async function DocumentsAdminPage() {
  const { docs, error } = await loadDocuments()

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">文档管理</h1>
        <div className="flex-1">
          <Button variant="outline" size="sm">
            <Link href="/">返回首页</Link>
          </Button>
        </div>
        <ReindexButton />
      </div>

      <p className="text-sm text-muted-foreground">
        将 Word 文档（.docx）放入数据目录（docker compose 默认映射到{' '}
        <code className="rounded bg-muted px-1">docker-compose/data/inbox</code>）后点击重建索引。
      </p>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted-foreground">
            <th className="py-2">文件名</th>
            <th>分块数</th>
            <th>状态</th>
            <th>索引时间</th>
          </tr>
        </thead>
        <tbody>
          {docs.length === 0 && !error && (
            <tr>
              <td colSpan={4} className="py-6 text-center text-muted-foreground">
                尚未索引任何文档，请放入 .docx 文件后点击「扫描文件夹并重建索引」。
              </td>
            </tr>
          )}
          {docs.map((d) => (
            <tr key={d.filename} className="border-b border-border">
              <td className="py-2">{d.filename}</td>
              <td>{d.chunkCount}</td>
              <td>
                <Badge>已索引</Badge>
              </td>
              <td>{formatBeijingTime(d.updatedAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
