# Deployment Guide

This guide covers deploying the G|Flows Frontend application to various platforms.

## Build for Production

Before deploying, create a production build:

\`\`\`bash
# Install dependencies
npm install

# Create production build
npm run build

# Test production build locally
npm start
\`\`\`

## Deployment Platforms

### Vercel (Recommended)

Vercel is the easiest way to deploy Next.js applications:

#### Automatic Deployment

1. **Connect Repository**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will automatically detect Next.js

2. **Configure Environment Variables**
   \`\`\`
   NEXT_PUBLIC_API_URL=https://your-domain.com
   NODE_ENV=production
   \`\`\`

3. **Deploy**
   - Push to main branch triggers automatic deployment
   - Preview deployments for pull requests

#### Manual Deployment

\`\`\`bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
\`\`\`

### Netlify

Deploy to Netlify with these settings:

1. **Build Settings**
   - Build command: `npm run build`
   - Publish directory: `.next`

2. **Environment Variables**
   \`\`\`
   NEXT_PUBLIC_API_URL=https://your-domain.com
   NODE_ENV=production
   \`\`\`

### Docker Deployment

#### Dockerfile

\`\`\`dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
\`\`\`

#### Docker Commands

\`\`\`bash
# Build image
docker build -t gflows-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://api.example.com gflows-frontend

# Using Docker Compose
docker-compose up -d
\`\`\`

#### docker-compose.yml

\`\`\`yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.example.com
      - NODE_ENV=production
    restart: unless-stopped
\`\`\`

### AWS Deployment

#### AWS Amplify

1. **Connect Repository**
   - Go to AWS Amplify Console
   - Connect your GitHub repository

2. **Build Settings**
   \`\`\`yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: .next
       files:
         - '**/*'
     cache:
       paths:
         - node_modules/**/*
   \`\`\`

#### AWS EC2

\`\`\`bash
# Connect to EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone and setup
git clone https://github.com/your-org/gflows-frontend.git
cd gflows-frontend
npm install
npm run build

# Install PM2 for process management
sudo npm install -g pm2

# Start application
pm2 start npm --name "gflows-frontend" -- start
pm2 startup
pm2 save
\`\`\`

### DigitalOcean App Platform

1. **Create App**
   - Connect GitHub repository
   - Select Node.js environment

2. **App Spec**
   \`\`\`yaml
   name: gflows-frontend
   services:
   - name: web
     source_dir: /
     github:
       repo: your-org/gflows-frontend
       branch: main
     run_command: npm start
     build_command: npm run build
     environment_slug: node-js
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: NEXT_PUBLIC_API_URL
       value: https://your-api-domain.com
   \`\`\`

## Environment Variables

### Required Variables

\`\`\`env
# Production API URL
NEXT_PUBLIC_API_URL=https://your-api-domain.com

# Environment
NODE_ENV=production
\`\`\`

### Optional Variables

\`\`\`env
# Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id

# Error Tracking
SENTRY_DSN=your-sentry-dsn

# Feature Flags
NEXT_PUBLIC_ENABLE_BETA_FEATURES=false
\`\`\`

## Performance Optimization

### Next.js Configuration

\`\`\`javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  compress: true,
  poweredByHeader: false,
  generateEtags: false,
  images: {
    domains: ['your-image-domain.com'],
  },
  headers: async () => [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'X-Frame-Options',
          value: 'DENY',
        },
        {
          key: 'X-Content-Type-Options',
          value: 'nosniff',
        },
      ],
    },
  ],
}

module.exports = nextConfig
\`\`\`

### CDN Configuration

For better performance, configure a CDN:

1. **Cloudflare**
   - Add your domain to Cloudflare
   - Enable caching for static assets
   - Configure SSL/TLS

2. **AWS CloudFront**
   - Create distribution pointing to your origin
   - Configure caching behaviors
   - Set up SSL certificate

## Monitoring and Logging

### Error Tracking

\`\`\`bash
# Install Sentry
npm install @sentry/nextjs

# Configure in next.config.js
const { withSentryConfig } = require('@sentry/nextjs')
\`\`\`

### Analytics

\`\`\`bash
# Install analytics
npm install @vercel/analytics

# Add to app/layout.tsx
import { Analytics } from '@vercel/analytics/react'
\`\`\`

## Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use platform-specific environment variable management
- Rotate secrets regularly

### Headers
- Configure security headers in `next.config.js`
- Use HTTPS in production
- Implement Content Security Policy (CSP)

### Dependencies
\`\`\`bash
# Audit dependencies regularly
npm audit

# Update dependencies
npm update

# Check for vulnerabilities
npm audit fix
\`\`\`

## Backup and Recovery

### Database Backups
If using a database, implement regular backups:

\`\`\`bash
# Example for PostgreSQL
pg_dump -h hostname -U username database_name > backup.sql
\`\`\`

### Code Backups
- Use Git for version control
- Maintain multiple deployment environments
- Tag releases for easy rollback

## Troubleshooting

### Common Deployment Issues

1. **Build Failures**
   \`\`\`bash
   # Check build logs
   npm run build
   
   # Verify dependencies
   npm ci
   \`\`\`

2. **Environment Variable Issues**
   - Verify all required variables are set
   - Check variable names (case-sensitive)
   - Ensure values are properly escaped

3. **Performance Issues**
   - Enable compression
   - Optimize images
   - Use CDN for static assets
   - Monitor bundle size

### Health Checks

Implement health check endpoints:

\`\`\`typescript
// app/api/health/route.ts
export async function GET() {
  return Response.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString() 
  })
}
\`\`\`

## Rollback Procedures

### Vercel
\`\`\`bash
# List deployments
vercel ls

# Promote previous deployment
vercel promote [deployment-url]
\`\`\`

### Docker
\`\`\`bash
# Tag current version
docker tag gflows-frontend:latest gflows-frontend:v1.0.0

# Rollback to previous version
docker run -p 3000:3000 gflows-frontend:v0.9.0
\`\`\`

This deployment guide should help you successfully deploy the G|Flows Frontend to your preferred platform.
