# ─────────────────────────────────────────────────────────────────────────────
# CarbonTracker AI — Frontend Dockerfile
# Next.js 14 Production Build (standalone output)
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Dependencies
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

# Copy package manifests
COPY package.json package-lock.json* ./

# Install production dependencies
RUN npm ci --only=production


# Stage 2: Builder — compile Next.js app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy all dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Set build-time environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
# Backend API URL for server-side requests in production
ARG NEXT_PUBLIC_API_URL=http://backend:8001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application (standalone output for Docker)
RUN npm run build


# Stage 3: Runtime — minimal production image
FROM node:20-alpine AS runtime

LABEL maintainer="CarbonTracker AI Team"
LABEL version="1.0.0"
LABEL description="CarbonTracker AI Frontend — Next.js 14 Production Server"

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 carbontracker \
    && adduser --system --uid 1001 carbontracker

# Copy only what is needed for runtime
COPY --from=builder --chown=carbontracker:carbontracker /app/public ./public
COPY --from=builder --chown=carbontracker:carbontracker /app/.next/standalone ./
COPY --from=builder --chown=carbontracker:carbontracker /app/.next/static ./.next/static

USER carbontracker

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
