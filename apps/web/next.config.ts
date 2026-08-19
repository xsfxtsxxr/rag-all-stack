import dotenv from 'dotenv'
import type { NextConfig } from 'next'
import path from 'node:path'

// 全项目共用仓库根目录唯一环境文件 .env
// （Next.js 默认只读本应用目录的 .env.local，此处显式加载根目录配置）
dotenv.config({ path: path.resolve(__dirname, '../../.env') })

const nextConfig: NextConfig = {
  // 工作区内的 TS 源码包需要转译
  transpilePackages: ['@rag/database', '@rag/shared-types'],
}

export default nextConfig
