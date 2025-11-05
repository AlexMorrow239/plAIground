# Legal AI Research Sandbox Frontend Container
# Multi-stage build for production optimization

FROM docker.io/oven/bun:1-alpine AS deps

# Install dependencies only when needed
WORKDIR /app

# Copy dependency files
COPY package.json bun.lock ./

# Install dependencies using bun
RUN bun install --frozen-lockfile --production

FROM docker.io/oven/bun:1-alpine AS builder

WORKDIR /app

# Copy dependency files and install all dependencies (including dev)
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Build arguments for API URLs
ARG NEXT_PUBLIC_API_URL=http://localhost:8000

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application (without turbopack for better container compatibility)
RUN bun run next build

FROM docker.io/oven/bun:1-alpine AS runner

# Install wget for health check
RUN apk add --no-cache wget

# Security: Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy built application
COPY --from=builder /app/public ./public

# Set correct ownership for precompiled builds
RUN mkdir .next && chown nextjs:nodejs .next

# Copy built application files
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run the application
CMD ["bun", "server.js"]
