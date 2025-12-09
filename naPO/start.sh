#!/bin/bash
echo "🚀 Starting naPO..."
echo ""
echo "1️⃣ Setting up database..."
cd apps/backend && ./setup_db.sh
cd ../..

echo ""
echo "2️⃣ Starting development servers..."
pnpm dev
