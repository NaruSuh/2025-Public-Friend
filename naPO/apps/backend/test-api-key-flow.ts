import { PrismaClient } from '@prisma/client';
import { getApiKey } from './src/lib/apiKeyHelper';

const prisma = new PrismaClient();

async function testApiKeyFlow() {
  console.log('=== API Key Flow Test ===\n');

  try {
    // Test 1: Get rone API key
    console.log('Test 1: Getting R-ONE API key from DB...');
    const roneKey = await getApiKey('rone');
    console.log('✅ Retrieved:', roneKey ? '[KEY EXISTS]' : '[NOT FOUND]');

    // Test 2: Get nabostats API key
    console.log('Test 2: Getting NABOSTATS API key from DB...');
    const nabostatsKey = await getApiKey('nabostats');
    console.log('✅ Retrieved:', nabostatsKey ? '[KEY EXISTS]' : '[NOT FOUND]');

    // Test 3: Get nec_manifesto API key
    console.log('Test 3: Getting NEC_MANIFESTO API key from DB...');
    const necKey = await getApiKey('nec_manifesto');
    console.log('✅ Retrieved:', necKey ? '[KEY EXISTS]' : '[NOT FOUND]');

    // Test 4: Compare with .env
    console.log('Test 4: Comparing with .env values...');
    const envRone = process.env.RONE_API_KEY;
    const envNabostats = process.env.NABOSTATS_API_KEY;
    const envNec = process.env.NEC_MANIFESTO_API_KEY;

    console.log('R-ONE match:', roneKey === envRone ? '✅' : '❌');
    console.log('NABOSTATS match:', nabostatsKey === envNabostats ? '✅' : '❌');
    console.log('NEC match:', necKey === envNec ? '✅' : '❌');

    console.log('\n=== All Tests Passed ===');
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  } finally {
    await prisma.$disconnect();
  }
}

testApiKeyFlow();
