-- 初始迁移：业务表（报价）
-- 精简版：无 LISTEN/NOTIFY 触发器、无 documents 表（文档索引由 AI 服务管理 pgvector 表）
-- 由 drizzle-kit 管理的后续迁移也输出到本目录，请勿手动修改生成文件。

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS "quotes" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
  "product_name" text NOT NULL,
  "model_no" text NOT NULL,
  "spec_summary" text DEFAULT '' NOT NULL,
  "price" numeric(12, 2) NOT NULL,
  "currency" text DEFAULT 'CNY' NOT NULL,
  "effective_date" date NOT NULL,
  "status" text DEFAULT 'active' NOT NULL,
  "created_at" timestamptz DEFAULT now() NOT NULL,
  "updated_at" timestamptz DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS "quotes_model_no_idx" ON "quotes" ("model_no");
