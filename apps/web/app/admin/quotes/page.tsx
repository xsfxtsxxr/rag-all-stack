'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { Quote, QuoteStatus } from '@rag/shared-types'
import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

interface QuoteForm {
  productName: string
  modelNo: string
  specSummary: string
  price: string
  currency: string
  effectiveDate: string
  status: QuoteStatus
}

const emptyForm: QuoteForm = {
  productName: '',
  modelNo: '',
  specSummary: '',
  price: '',
  currency: 'CNY',
  effectiveDate: '',
  status: 'active',
}

export default function QuotesAdminPage() {
  const [rows, setRows] = useState<Quote[]>([])
  const [form, setForm] = useState<QuoteForm>(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (): Promise<void> => {
    const res = await fetch('/api/quotes', { cache: 'no-store' })
    if (res.ok) setRows((await res.json()) as Quote[])
    setLoading(false)
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  function patch<K extends keyof QuoteForm>(key: K, value: QuoteForm[K]): void {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    if (!form.productName || !form.modelNo || !form.price || !form.effectiveDate) return
    const url = editingId ? `/api/quotes/${editingId}` : '/api/quotes'
    const method = editingId ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (res.ok) {
      setForm(emptyForm)
      setEditingId(null)
      await load()
    }
  }

  async function handleDelete(id: string): Promise<void> {
    const res = await fetch(`/api/quotes/${id}`, { method: 'DELETE' })
    if (res.ok) await load()
  }

  function startEdit(q: Quote): void {
    setEditingId(q.id)
    setForm({
      productName: q.productName,
      modelNo: q.modelNo,
      specSummary: q.specSummary,
      price: q.price,
      currency: q.currency,
      effectiveDate: q.effectiveDate.slice(0, 10),
      status: q.status,
    })
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">报价管理</h1>
        <Button variant="outline" size="sm">
          <Link href="/">返回首页</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{editingId ? '编辑报价' : '新增报价'}</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => void handleSubmit(e)}
            className="grid grid-cols-2 gap-3 md:grid-cols-4"
          >
            <Input
              placeholder="产品名称"
              value={form.productName}
              onChange={(e) => patch('productName', e.target.value)}
              required
            />
            <Input
              placeholder="型号"
              value={form.modelNo}
              onChange={(e) => patch('modelNo', e.target.value)}
              required
            />
            <Input
              placeholder="价格"
              value={form.price}
              onChange={(e) => patch('price', e.target.value)}
              required
            />
            <Input
              placeholder="币种"
              value={form.currency}
              onChange={(e) => patch('currency', e.target.value)}
              required
            />
            <Input
              placeholder="规格简述"
              className="col-span-2"
              value={form.specSummary}
              onChange={(e) => patch('specSummary', e.target.value)}
            />
            <Input
              type="date"
              value={form.effectiveDate}
              onChange={(e) => patch('effectiveDate', e.target.value)}
              required
            />
            <select
              className="h-9 rounded-md border border-border bg-card px-3 text-sm"
              value={form.status}
              onChange={(e) => patch('status', e.target.value as QuoteStatus)}
            >
              <option value="active">生效中</option>
              <option value="draft">草稿</option>
              <option value="inactive">已停用</option>
            </select>
            <div className="col-span-2 flex gap-2 md:col-span-4">
              <Button type="submit">{editingId ? '保存' : '新增'}</Button>
              {editingId && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setEditingId(null)
                    setForm(emptyForm)
                  }}
                >
                  取消
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">报价列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">加载中…</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2">产品</th>
                  <th>型号</th>
                  <th>价格</th>
                  <th>有效期</th>
                  <th>状态</th>
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((q) => (
                  <tr key={q.id} className="border-b border-border">
                    <td className="py-2">{q.productName}</td>
                    <td>{q.modelNo}</td>
                    <td>
                      {q.price} {q.currency}
                    </td>
                    <td>{q.effectiveDate.slice(0, 10)}</td>
                    <td>
                      <Badge>{q.status}</Badge>
                    </td>
                    <td className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => startEdit(q)}>
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600"
                        onClick={() => void handleDelete(q.id)}
                      >
                        删除
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
