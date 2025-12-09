import { PrismaClient } from '@prisma/client';
import { PartyPolicyService } from './src/services/api/partyPolicyService';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function testPartyPolicy() {
  console.log('\n=== Testing Party Policy API (Simple) ===\n');

  try {
    // Get API key from environment
    const apiKey = process.env.NEC_CANDIDATE_API_KEY || process.env.NEC_MANIFESTO_API_KEY;
    if (!apiKey) {
      throw new Error('NEC API key not found in .env');
    }

    console.log('API Key loaded:', apiKey.substring(0, 10) + '...');

    const electionId = '20220309'; // 2022 대통령선거

    // Test 1: Get party policy for 국민의힘
    console.log('\n[Test 1] Fetching party policy for 국민의힘...');
    const ppp = await PartyPolicyService.getPartyPolicy(apiKey, electionId, '국민의힘');

    console.log('\n=== FINAL RESULT ===');
    console.log(JSON.stringify(ppp, null, 2));

  } catch (error: any) {
    console.error('\n✗ Test failed:', error.message);
  } finally {
    await prisma.$disconnect();
  }

  console.log('\n=== Test Complete ===\n');
}

testPartyPolicy().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
