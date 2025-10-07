FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install --no-cache

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Accept build arguments for NEXT_PUBLIC_ environment variables
# These are embedded into the client-side JavaScript bundle at build time
ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_RABBITMQ_WS_URL=/rabbitmq/ws

# Set environment variables for the build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_RABBITMQ_WS_URL=$NEXT_PUBLIC_RABBITMQ_WS_URL

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED=1

# Build the Next.js application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install only http-proxy which our custom server needs for WebSocket proxying
# The standalone build doesn't include this dependency
# dotenv is NOT needed in production as env vars come from ConfigMap
COPY --from=builder /app/package.json ./
RUN npm install --production --no-cache http-proxy

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy our custom server.js AFTER the standalone files to override the default server.js
# The standalone build includes its own server.js which we need to replace
COPY --from=builder --chown=nextjs:nodejs /app/server.js ./server.js

USER nextjs

EXPOSE 3000

ENV PORT=3000

CMD ["node", "server.js"]
