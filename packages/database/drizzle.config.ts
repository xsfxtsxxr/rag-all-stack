import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  dialect: 'postgresql',
  schema: './schema/index.ts',
  out: './migrations',
  dbCredentials: {
    url:
      process.env.DATABASE_URL ??
      'postgres://rag_all_stack_db:rag_all_stack_db@localhost:55432/rag_all_stack_db',
  },
})
