import { create } from 'zustand'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatState {
  messages: ChatMessage[]
  sending: boolean
  send: (question: string) => Promise<void>
  clear: () => void
}

/** 打字机节奏：每 tick 从缓冲队列释放到界面上的字符数 */
const TYPEWRITER_TICK_MS = 30
const TYPEWRITER_CHARS_PER_TICK = 2

/**
 * 通过 SSE 读取 /api/ask 的流式回答。
 *
 * 上游 LLM（如 z.ai glm-5.3）会先推理再把 content 一次性成块吐出，
 * 浏览器一次 read() 就拿到几十个 token，直接写入会整段闪现。
 * 因此这里先把到达的 token 进缓冲，再由定时器逐字写入界面，
 * 保证无论上游按 token 还是按块到达，前端都是打字机效果。
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sending: false,

  send: async (question) => {
    set((s) => ({
      messages: [
        ...s.messages,
        { role: 'user', content: question },
        { role: 'assistant', content: '' },
      ],
      sending: true,
    }))

    // 网络侧按块到达，先入队；定时器逐字释放，结束后收尾
    let pending = ''
    let streamEnded = false
    const timer = setInterval(() => {
      const release = pending.slice(0, TYPEWRITER_CHARS_PER_TICK)
      pending = pending.slice(TYPEWRITER_CHARS_PER_TICK)
      if (release) {
        set((s) => {
          const msgs = [...s.messages]
          const last = msgs[msgs.length - 1]
          if (last) msgs[msgs.length - 1] = { ...last, content: last.content + release }
          return { messages: msgs }
        })
      } else if (streamEnded) {
        clearInterval(timer)
        set({ sending: false })
      }
    }, TYPEWRITER_TICK_MS)

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok || !res.body) throw new Error(`问答接口返回 ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue
          const payload = trimmed.slice(5).trim()
          if (payload === '[DONE]') continue
          try {
            const data = JSON.parse(payload) as { token?: string }
            if (typeof data.token === 'string') pending += data.token
          } catch {
            // 单行解析失败不影响后续流
          }
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : '未知错误'
      pending += `

出错了：${msg}`
    } finally {
      streamEnded = true
    }
  },

  clear: () => set({ messages: [] }),
}))
