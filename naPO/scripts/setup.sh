#!/bin/bash
set -e

echo "🔧 naPO - Initial Setup"
echo "========================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "📦 Installing pnpm..."; npm install -g pnpm; }
command -v docker >/dev/null 2>&1 || { echo "⚠️  Docker is not installed. Local PostgreSQL will not be available."; }

echo "✅ Prerequisites OK"

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install

# Setup environment files
echo "🔐 Setting up environment files..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Created .env file. Please update with your API keys."
fi

if [ ! -f "apps/backend/.env" ]; then
    cp .env.example apps/backend/.env
fi

# Start database
if command -v docker >/dev/null 2>&1; then
    echo "🐘 Starting PostgreSQL..."
    docker-compose up -d postgres

    # Wait for database
    echo "⏳ Waiting for database to be ready..."
    sleep 5

    # Run migrations
    echo "🔄 Running database migrations..."
    pnpm db:push
fi

echo "========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys:"
echo "   - OPENAI_API_KEY"
echo "   - PUBLIC_DATA_API_KEY"
echo "   - DATABASE_URL (if using Supabase)"
echo ""
echo "2. Start the development server:"
echo "   pnpm dev"
echo ""
echo "3. Open http://localhost:5173 in your browser"
