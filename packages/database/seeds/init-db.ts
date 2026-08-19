import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { Pool } from 'pg'

/** 应用 migrations/0000_init.sql（幂等），初始化表结构 */
async function main(): Promise<void> {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  const sql = readFileSync(join(process.cwd(), 'migrations/0000_init.sql'), 'utf8')
  await pool.query(sql)
  console.log('数据库初始化完成（quotes 表 + pgvector 扩展）')
  await pool.end()
}

void main().catch((err: unknown) => {
  console.error(err)
  process.exit(1)
})
