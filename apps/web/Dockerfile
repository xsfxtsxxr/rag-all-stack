FROM node:24-alpine AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable && corepack prepare pnpm@11.22.0 --activate
WORKDIR /app

FROM base AS deps

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/database/package.json packages/database/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json
COPY tooling/eslint-config/package.json tooling/eslint-config/package.json
COPY tooling/prettier-config/package.json tooling/prettier-config/package.json
COPY tooling/typescript-config/package.json tooling/typescript-config/package.json

RUN pnpm install --frozen-lockfile

FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN pnpm --filter @rag/web build

FROM base AS runner

ENV NODE_ENV=production

WORKDIR /app

COPY --from=builder --chown=node:node /app /app

USER node

EXPOSE 3000

CMD ["pnpm", "--filter", "@rag/web", "start"]
