import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function setupNecCommonCodeDB() {
  console.log('\n=== Setting up NEC Common Code API in Database ===\n');

  try {
    // Check if API source already exists
    const existing = await prisma.apiSource.findFirst({
      where: { name: 'public_data_common_code' },
    });

    if (existing) {
      console.log('✓ API source already exists:', existing.name);
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
        console.log('✓ API key already exists');
        console.log('  - Key preview:', apiKey.keyValue.substring(0, 10) + '...');
      } else {
        console.log('✗ API key not found, creating...');
        await createApiKey(existing.id);
      }
    } else {
      console.log('Creating new API source: public_data_common_code');

      // Create API source
      const apiSource = await prisma.apiSource.create({
        data: {
          name: 'public_data_common_code',
          displayName: '중앙선거관리위원회_코드관리',
          baseUrl: 'http://apis.data.go.kr/9760000/CommonCodeService',
          authType: 'API_KEY',
          authConfig: {
            keyParamName: 'ServiceKey',
            keyLocation: 'query',
          },
          responseFormat: 'JSON',
          rateLimit: {
            requestsPerMinute: 100,
            requestsPerDay: 10000,
          },
          isActive: true,
        },
      });

      console.log('✓ API source created:', apiSource.name);
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
  // Use the same NEC API key (they share the same key)
  const apiKey = process.env.NEC_CANDIDATE_API_KEY || process.env.NEC_MANIFESTO_API_KEY;

  if (!apiKey) {
    console.error('✗ NEC API key not found in .env file');
    console.error('  Please set NEC_CANDIDATE_API_KEY or NEC_MANIFESTO_API_KEY');
    throw new Error('NEC API key is required');
  }

  const key = await prisma.apiKey.create({
    data: {
      sourceId,
      keyValue: apiKey, // Stored as plaintext (encryption disabled)
      isActive: true,
      expiresAt: null, // No expiration
    },
  });

  console.log('✓ API key created');
  console.log('  - Key preview:', key.keyValue.substring(0, 10) + '...');
  console.log('  - Is active:', key.isActive);
}

setupNecCommonCodeDB().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
