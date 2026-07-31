# syntax=docker/dockerfile:1.7
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

FROM node:24-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 \
    NODE_OPTIONS=--max-old-space-size=384 \
    HOSTNAME=0.0.0.0
# npm в рантайме не нужен: standalone-сборка запускается голым node.
# Удаление убирает из образа целый пласт CVE в его собственных зависимостях
# (tar, brace-expansion и прочие), которые мы иначе не контролируем.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx \
 && addgroup -g 10001 nodejs && adduser -u 10001 -G nodejs -S nextjs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
# В Alpine стоит busybox wget: он НЕ понимает --max-redirect и --spider
# из GNU wget и падает на разборе аргументов, а не на запросе.
# Поэтому проверяем /ru напрямую, без редиректов, самой простой формой.
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/ru || exit 1
CMD ["node", "server.js"]
