'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useState } from 'react'
import { useChatStore } from './store'

export function Chat() {
  const messages = useChatStore((s) => s.messages)
  const sending = useChatStore((s) => s.sending)
  const send = useChatStore((s) => s.send)
  const clear = useChatStore((s) => s.clear)
  const [input, setInput] = useState('')

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    const question = input.trim()
    if (!question || sending) return
    setInput('')
    await send(question)
  }

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col gap-4 p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">工业销售询盘知识库</h1>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={clear}>
            清空
          </Button>
        </div>
      </header>

      <section className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="pt-16 text-center text-sm text-muted-foreground">
            输入询盘问题，例如：你们有没有 22kW 的变频器？价格多少？
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <Card
              className={
                m.role === 'user' ? 'max-w-[80%] bg-primary text-primary-foreground' : 'max-w-[80%]'
              }
            >
              <CardContent className="whitespace-pre-wrap px-4 py-2 text-sm">
                {m.content || (sending && i === messages.length - 1 ? '思考中…' : '')}
              </CardContent>
            </Card>
          </div>
        ))}
      </section>

      <form onSubmit={(e) => void handleSubmit(e)} className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的询盘问题…"
          disabled={sending}
        />
        <Button type="submit" disabled={sending || !input.trim()}>
          发送
        </Button>
      </form>
    </main>
  )
}
