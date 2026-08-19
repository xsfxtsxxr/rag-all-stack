import { quotes } from '@rag/database/schema'
import { drizzle } from 'drizzle-orm/node-postgres'
import { Pool } from 'pg'

/** 开发调试用示例报价（固定 id，重复执行幂等） */
const samples: (typeof quotes.$inferInsert)[] = [
  {
    id: '10000000-0000-4000-8000-000000000001',
    productName: '工业变频器',
    modelNo: 'VFD-220',
    specSummary: '380V/22kW 通用型矢量变频器，防护等级 IP54，支持 Modbus 通讯',
    price: '5800.00',
    currency: 'CNY',
    effectiveDate: new Date('2026-09-01'),
    status: 'active',
  },
  {
    id: '10000000-0000-4000-8000-000000000002',
    productName: '伺服电机',
    modelNo: 'SVM-750W',
    specSummary: '750W 交流伺服电机，额定转矩 2.39N·m，配 17 位编码器',
    price: '2350.00',
    currency: 'CNY',
    effectiveDate: new Date('2026-09-01'),
    status: 'active',
  },
  {
    id: '10000000-0000-4000-8000-000000000003',
    productName: 'PLC 控制器',
    modelNo: 'PLC-1200',
    specSummary: '14DI/10DO，2 路模拟量输入，支持 Profinet/以太网',
    price: '1680.00',
    currency: 'CNY',
    effectiveDate: new Date('2026-08-01'),
    status: 'active',
  },
  {
    id: '10000000-0000-4000-8000-000000000004',
    productName: '触摸屏',
    modelNo: 'HMI-10',
    specSummary: '10.1 寸工业触摸屏，分辨率 1024x600，支持配方与趋势图',
    price: '1290.00',
    currency: 'CNY',
    effectiveDate: new Date('2026-07-01'),
    status: 'draft',
  },
]

async function main(): Promise<void> {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  const db = drizzle(pool)
  await db.insert(quotes).values(samples).onConflictDoNothing()
  console.log(`示例报价写入完成（已存在则跳过，共 ${samples.length} 条）`)
  await pool.end()
}

void main().catch((err: unknown) => {
  console.error(err)
  process.exit(1)
})
