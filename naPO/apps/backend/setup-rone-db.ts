import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function setupRoneDB() {
  console.log('\n=== Setting up R-ONE API in Database ===\n');

  try {
    // Check if API source already exists
    const existing = await prisma.apiSource.findFirst({
      where: { name: 'rone' },
    });

    if (existing) {
      console.log(' API source already exists:', existing.name);
      console.log('  - ID:', existing.id);
      console.log('  - Display Name:', existing.displayName);

      // Check if API key exists
      const apiKey = await prisma.apiKey.findFirst({
        where: {
          sourceId: existing.id,
          isActive: true,
        },
      });

      if (apiKey) {
        console.log(' API key already exists');
        console.log('  - Key preview:', apiKey.keyValue.substring(0, 10) + '...');
      } else {
        console.log(' API key not found, creating...');
        await createApiKey(existing.id);
      }
    } else {
      console.log('Creating new API source: rone');

      // Create API source
      const apiSource = await prisma.apiSource.create({
        data: {
          name: 'rone',
          displayName: 'R-ONE €Ù°µÄô',
          baseUrl: 'https://www.reb.or.kr/r-one/openapi',
          authType: 'API_KEY',
          authConfig: {
            keyParamName: 'KEY',
            keyLocation: 'query',
          },
          responseFormat: 'JSON',
          endpoints: {
            getTableList: '/SttsApiTbl.do',
            getTableItems: '/SttsApiTblItm.do',
            getTableData: '/SttsApiTblData.do',
          },
          defaultParams: {
            Type: 'json',
            pIndex: '1',
            pSize: '100',
          },
          isActive: true,
        },
      });

      console.log(' API source created:', apiSource.name);
      console.log('  - ID:', apiSource.id);

      // Create API key
      await createApiKey(apiSource.id);
    }

    console.log('\n=== Setup Complete ===\n');
  } catch (error) {
    console.error('Setup failed:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

async function createApiKey(sourceId: string) {
  const apiKey = process.env.RONE_API_KEY;

  if (!apiKey) {
    console.error(' R-ONE API key not found in .env file');
    console.error('  Please set RONE_API_KEY in your .env file');
    throw new Error('RONE_API_KEY is required');
  }

  const key = await prisma.apiKey.create({
    data: {
      sourceId,
      keyValue: apiKey, // Stored as plaintext (encryption disabled)
      isActive: true,
      expiresAt: null, // No expiration
    },
  });

  console.log(' API key created');
  console.log('  - Key preview:', key.keyValue.substring(0, 10) + '...');
  console.log('  - Is active:', key.isActive);
}

setupRoneDB().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
