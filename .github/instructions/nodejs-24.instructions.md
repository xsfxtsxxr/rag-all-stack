---
description: "编写或修改 Nodejs 代码、管理依赖（pnpm）、格式化与静态检查（ESLint/Prettier）、类型标注（TypeScript）、编写测试（Jest）。适用于所有 .ts 文件。"
applyTo: "**/*.ts"
---

## 1. 环境与工具链

- 目标解释器：**Node.js 24.x**，依赖管理用 **pnpm**（`package.json` + `pnpm-lock.yaml`）。
- 新增依赖：运行时 `pnpm add <pkg>`；开发依赖 `pnpm add -D <pkg>`。**禁止**手写 `package-lock.json`、混用 `npm install` / `yarn add` 装业务依赖。
- 全部工具配置（ESLint / Prettier / Jest / tsconfig）集中在 `package.json` 或对应配置文件，不散落 `.eslintrc`/`.prettierrc`。
- 格式化与 lint 由 **ESLint/Prettier** 承担（`eslint --fix` + `prettier --write`），不再引入其他工具。
- `pnpm-lock.yaml` 必须提交。

## 2. TypeScript 严格模式

- 所有 tsconfig 开启 `"strict": true`，并补充 `noUncheckedIndexedAccess`、`noImplicitOverride`、`noFallthroughCasesInSwitch`。
- 禁止裸 `any`；确实无法推断时用 `unknown` + 类型收窄，或通过 `zod` schema 推导业务类型。
- 所有导出函数必须显式声明参数与返回值类型；跨包共享类型统一放在 `packages/shared-types`，禁止在 `apps/web` 与 `apps/sync-worker` 之间复制类型定义。
- 接口出入参校验统一用 `zod`，避免手写类型守卫。

## 3. 代码风格（ESLint + Prettier）

- ESLint 使用 Flat Config（`eslint.config.mjs`），集成 `typescript-eslint`；统一规则放 `tooling/eslint-config`，各应用只引用不复制。
- Prettier 配置统一放 `tooling/prettier-config`，全仓同一份，禁止各包覆盖。
- tsconfig 继承 `tooling/typescript-config` 的 `base.json` / `nextjs.json` / `node.json`，禁止各应用自建散乱配置。
- 提交前运行 `pnpm lint`（eslint --fix）与 `pnpm format`（prettier --write）。
- 导入顺序：Node 内置 → 第三方 → 工作区包（`@rag/*`）→ 相对路径。

## 4. 测试（Jest）

- 统一使用 Jest（`ts-jest`），配置集中在根目录或各包 `jest.config.ts`；禁止混用 Vitest。
- 单测文件命名 `*.test.ts`，放在 `src/__tests__/` 或与被测文件同目录。
- 队列、检索、同步等关键业务逻辑必须覆盖核心分支；测试内禁止真实网络/数据库调用，使用 mock。
- 运行：根目录 `pnpm test`，单包 `pnpm --filter <pkg> test`。

## 5. Monorepo 约定（pnpm + Turborepo）

- 安装依赖必须指定包：`pnpm --filter @rag/web add <pkg>`；公共工具（typescript、eslint、prettier、jest）提升到根 `devDependencies` 统一版本。
- 工作区包命名统一 `@rag/*`（含 `@rag/eslint-config`、`@rag/typescript-config` 等 tooling 包）。
- `services/` 下的 Python 服务由 Poetry 管理，**不属于 pnpm 工作区**，禁止在其中执行 pnpm 命令。
- Turborepo 任务命名：`build`、`lint`、`test`、`dev`、`typecheck`；跨包依赖在 `turbo.json` 用 `dependsOn`（如 `^build`）声明。
