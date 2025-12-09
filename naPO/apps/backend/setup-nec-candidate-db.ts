import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function setupNecCandidateDB() {
  console.log('\n=== Setting up NEC Candidate API in Database ===\n');

  try {
    // Check if API source already exists
    const existing = await prisma.apiSource.findFirst({
      where: { name: 'public_data_candidate' },
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
      console.log('Creating new API source: public_data_candidate');

      // Create API source
      const apiSource = await prisma.apiSource.create({
        data: {
          name: 'public_data_candidate',
          displayName: '중앙선거관리위원회_후보자정보',
          baseUrl: 'http://apis.data.go.kr/9760000/PofelcddInfoInqireService',
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
  const apiKey = process.env.NEC_CANDIDATE_API_KEY;

  if (!apiKey) {
    console.error('✗ NEC_CANDIDATE_API_KEY not found in .env file');
    throw new Error('NEC_CANDIDATE_API_KEY is required');
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

setupNecCandidateDB().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
