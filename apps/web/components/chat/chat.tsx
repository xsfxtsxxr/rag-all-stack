'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Paperclip, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { DEFAULT_IMAGE_QUESTION, useChatStore } from './store'

export function Chat() {
  const messages = useChatStore((s) => s.messages)
  const sending = useChatStore((s) => s.sending)
  const image = useChatStore((s) => s.image)
  const send = useChatStore((s) => s.send)
  const setImage = useChatStore((s) => s.setImage)
  const clear = useChatStore((s) => s.clear)
  const [input, setInput] = useState('')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 组件卸载时释放 Object URL，避免内存泄漏
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  function clearPreview(): void {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
  }

  function handlePickImage(e: React.ChangeEvent<HTMLInputElement>): void {
    const file = e.target.files?.[0]
    if (!file) return
    clearPreview()
    setImage(file)
    setPreviewUrl(URL.createObjectURL(file))
    // 上传后自动填入默认提问，用户可直接发送或修改
    setInput(DEFAULT_IMAGE_QUESTION)
    // 清空 input.value，允许重复选择同一文件
    e.target.value = ''
  }

  function removeImage(): void {
    clearPreview()
    setImage(null)
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    if (sending) return
    const question = input.trim()
    if (!question && !image) return
    setInput('')
    const succeeded = await send(question || DEFAULT_IMAGE_QUESTION)
    if (succeeded) clearPreview()
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
            <br />
            也可以点击输入框旁的按钮上传技术规格参数截图。
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

      <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-2">
        {image && previewUrl && (
          <div className="flex items-center gap-2 rounded-md border bg-background p-2">
            <img
              src={previewUrl}
              alt="规格参数截图预览"
              className="h-14 w-14 rounded object-cover"
            />
            <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">
              {image.name}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={removeImage}
              aria-label="移除图片"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handlePickImage}
            disabled={sending}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="px-2"
            disabled={sending}
            onClick={() => fileInputRef.current?.click()}
            aria-label="上传规格参数截图"
            title="上传规格参数截图"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入你的询盘问题…"
            disabled={sending}
          />
          <Button type="submit" disabled={sending || (!input.trim() && !image)}>
            发送
          </Button>
        </div>
      </form>
    </main>
  )
}
