import { PrismaClient } from '@prisma/client';

// Prevent multiple Prisma Client instances in development
declare global {
  // eslint-disable-next-line no-var
  var __prisma: PrismaClient | undefined;
}

// Guard: skip Prisma when DATABASE_URL is not configured (e.g. HF Spaces)
const hasDatabase =
  process.env.DATABASE_URL &&
  process.env.DATABASE_URL !== 'postgresql://skip:skip@localhost:5432/skip';

function createPrismaClient(): PrismaClient {
  if (!hasDatabase) {
    // Return a no-op proxy that returns empty results (HF Spaces / demo mode)
    const noopModel = new Proxy(
      {},
      {
        get(_, method) {
          // Read operations → return empty results
          if (method === 'findMany') return () => Promise.resolve([]);
          if (method === 'findFirst' || method === 'findUnique') return () => Promise.resolve(null);
          if (method === 'count') return () => Promise.resolve(0);
          // Write operations → silently succeed
          if (method === 'create' || method === 'update' || method === 'upsert')
            return () => Promise.resolve({});
          if (method === 'createMany' || method === 'updateMany' || method === 'deleteMany')
            return () => Promise.resolve({ count: 0 });
          if (method === 'delete') return () => Promise.resolve({});
          // Anything else → resolve empty
          return () => Promise.resolve(null);
        },
      }
    );

    return new Proxy({} as PrismaClient, {
      get(_, prop) {
        if (prop === '$disconnect' || prop === '$connect') return () => Promise.resolve();
        if (prop === '$transaction') return (fn: any) => (typeof fn === 'function' ? fn({}) : Promise.resolve([]));
        if (prop === 'then') return undefined;
        // Every model access (prisma.user, prisma.apiSource, etc.) → noopModel
        return noopModel;
      },
    });
  }

  return (
    global.__prisma ||
    new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
    })
  );
}

export const prisma: PrismaClient = createPrismaClient();
export { hasDatabase };

if (process.env.NODE_ENV !== 'production' && hasDatabase) {
  global.__prisma = prisma;
}

// Graceful shutdown
process.on('beforeExit', async () => {
  if (hasDatabase) {
    await prisma.$disconnect();
  }
});
