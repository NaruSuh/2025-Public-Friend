#!/bin/bash
export PGPASSWORD=postgres
psql -h localhost -U postgres -d postgres -c "CREATE DATABASE napo_dev;" 2>/dev/null || echo "Database already exists"
npx prisma db push
echo "✅ Database setup complete!"
