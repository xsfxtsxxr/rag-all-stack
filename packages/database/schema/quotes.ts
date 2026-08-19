import { date, index, numeric, pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core'

export const quotes = pgTable(
  'quotes',
  {
    id: uuid('id').defaultRandom().primaryKey(),
    productName: text('product_name').notNull(),
    modelNo: text('model_no').notNull(),
    specSummary: text('spec_summary').notNull().default(''),
    price: numeric('price', { precision: 12, scale: 2 }).notNull(),
    currency: text('currency').notNull().default('CNY'),
    effectiveDate: date('effective_date', { mode: 'date' }).notNull(),
    status: text('status').notNull().default('active'),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [index('quotes_model_no_idx').on(table.modelNo)],
)
