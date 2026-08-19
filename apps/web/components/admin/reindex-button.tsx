'use client'

import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

/** 触发 AI 服务扫描文档文件夹并重建索引 */
export function ReindexButton() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  async function handleClick(): Promise<void> {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch('/api/sync', { method: 'POST' })
      const data = (await res.json()) as {
        documents?: number
        chunks?: number
        quotes?: number
        error?: string
      }
      if (!res.ok) throw new Error(data.error ?? `返回 ${res.status}`)
      setMessage(
        `完成：${data.documents ?? 0} 个文档 / ${data.chunks ?? 0} 个分块 / ${data.quotes ?? 0} 条报价`,
      )
      router.refresh()
    } catch (e) {
      setMessage(`失败：${e instanceof Error ? e.message : '未知错误'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <Button onClick={() => void handleClick()} disabled={loading}>
        {loading ? '索引中…' : '扫描文件夹并重建索引'}
      </Button>
      {message && <span className="text-sm text-muted-foreground">{message}</span>}
    </div>
  )
}
