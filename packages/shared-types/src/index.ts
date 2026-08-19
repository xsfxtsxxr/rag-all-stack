import { z } from 'zod'

// ===== 报价（quotes）=====

export const QuoteStatusSchema = z.enum(['active', 'inactive', 'draft'])
export type QuoteStatus = z.infer<typeof QuoteStatusSchema>

/** 报价新增/更新的入参校验 */
export const QuoteUpsertSchema = z.object({
  productName: z.string().min(1).max(200),
  modelNo: z.string().min(1).max(100),
  specSummary: z.string().max(2000).default(''),
  price: z.string().regex(/^\d+(\.\d{1,2})?$/, '价格需为数字（最多两位小数）'),
  currency: z.string().min(3).max(3).default('CNY'),
  effectiveDate: z.coerce.date(),
  status: QuoteStatusSchema.default('active'),
})
export type QuoteUpsert = z.infer<typeof QuoteUpsertSchema>

/** 报价资源（经过 JSON 序列化后的形态） */
export interface Quote {
  id: string
  productName: string
  modelNo: string
  specSummary: string
  price: string
  currency: string
  effectiveDate: string
  status: QuoteStatus
  createdAt: string
  updatedAt: string
}

/** 问答接口入参 */
export const AskRequestSchema = z.object({
  question: z.string().min(1).max(2000),
  history: z
    .array(z.object({ role: z.enum(['user', 'assistant']), content: z.string() }))
    .max(10)
    .optional(),
})
export type AskRequest = z.infer<typeof AskRequestSchema>

/** AI 服务全量重索引返回 */
export interface ReindexResult {
  documents: number
  chunks: number
  quotes: number
}
