#!/bin/bash
set -e

echo "🚀 naPO - Deployment Script"
echo "============================================="

# Check environment
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh [dev|staging|prod]"
    exit 1
fi

ENV=$1
echo "📦 Deploying to: $ENV"

# Load environment-specific variables
if [ -f ".env.$ENV" ]; then
    export $(cat .env.$ENV | xargs)
fi

case $ENV in
    dev)
        echo "🔧 Starting development environment..."
        docker-compose up -d postgres redis
        pnpm install
        pnpm db:push
        pnpm dev
        ;;

    staging)
        echo "🔧 Building for staging..."
        pnpm install
        pnpm build

        echo "🐳 Building Docker images..."
        docker-compose -f docker-compose.prod.yml build

        echo "🚀 Deploying to staging..."
        docker-compose -f docker-compose.prod.yml up -d
        ;;

    prod)
        echo "🔧 Building for production..."
        pnpm install --frozen-lockfile
        pnpm build

        echo "📤 Deploying to Vercel..."
        vercel --prod

        echo "✅ Production deployment complete!"
        ;;

    *)
        echo "❌ Unknown environment: $ENV"
        exit 1
        ;;
esac

echo "============================================="
echo "✅ Deployment complete!"
