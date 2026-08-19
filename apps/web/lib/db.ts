import * as schema from '@rag/database/schema'
import { drizzle, type NodePgDatabase } from 'drizzle-orm/node-postgres'
import { Pool } from 'pg'

/** 开发模式下跨热更新复用连接池 */
const globalForDb = globalThis as unknown as {
  pool?: Pool
  db?: NodePgDatabase<typeof schema>
}

function createDb(): NodePgDatabase<typeof schema> {
  const pool = new Pool({
    connectionString:
      process.env.DATABASE_URL ??
      'postgres://rag_all_stack_db:rag_all_stack_db@localhost:55432/rag_all_stack_db',
  })
  globalForDb.pool = pool
  return drizzle(pool, { schema })
}

export const db: NodePgDatabase<typeof schema> = globalForDb.db ?? createDb()
