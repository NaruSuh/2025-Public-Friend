import { PrismaClient } from '@prisma/client';
import { NecApiChainService } from './src/services/api/necApiChainService';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function testNecApiChain() {
  console.log('\n=== Testing NEC API Chain ===\n');

  try {
    // Get API key from environment
    const apiKey = process.env.NEC_CANDIDATE_API_KEY;
    if (!apiKey) {
      throw new Error('NEC_CANDIDATE_API_KEY not found in .env');
    }

    console.log('API Key loaded:', apiKey.substring(0, 10) + '...');

    // Test 1: Get all candidates for 2022 presidential election
    console.log('\n[Test 1] Fetching all candidates for 2022 presidential election...');
    const allCandidates = await NecApiChainService.getAllCandidates(
      '20220309',  // 2022년 대선
      '1',         // 대통령선거
      apiKey
    );

    if (allCandidates.success) {
      console.log(`✓ Found ${allCandidates.totalCount} candidates`);
      console.log('\nCandidate list:');
      allCandidates.data.slice(0, 5).forEach((candidate: any, index: number) => {
        console.log(`  ${index + 1}. ${candidate.nameKr} (${candidate.party}) - 기호 ${candidate.ballotNumber}`);
      });
    } else {
      console.error('✗ Failed to fetch candidates:', allCandidates.error);
    }

    // Test 2: Get pledges by candidate name (윤석열)
    console.log('\n[Test 2] Fetching pledges for 윤석열...');
    const yoonPledges = await NecApiChainService.getCandidatePledgesByName(
      '20220309',
      '1',
      '윤석열',
      apiKey
    );

    if (yoonPledges.success) {
      console.log('✓ API chain succeeded!');
      console.log('\nCandidate info:');
      console.log(`  - Name: ${yoonPledges.candidate.name}`);
      console.log(`  - Party: ${yoonPledges.candidate.party}`);
      console.log(`  - Ballot: ${yoonPledges.candidate.ballotNumber}`);
      console.log(`  - ID: ${yoonPledges.candidate.id}`);

      console.log('\nPledges:');
      if (yoonPledges.pledges.data && yoonPledges.pledges.data.length > 0) {
        yoonPledges.pledges.data.slice(0, 3).forEach((pledge: any, index: number) => {
          console.log(`  ${index + 1}. ${pledge.pledges?.[0]?.title || 'N/A'}`);
        });
      } else {
        console.log('  (No pledges found)');
      }
    } else {
      console.error('✗ API chain failed:', yoonPledges.error);
    }

    // Test 3: Get pledges for multiple candidates
    console.log('\n[Test 3] Fetching pledges for multiple candidates...');
    const multiplePledges = await NecApiChainService.getMultipleCandidatesPledges(
      '20220309',
      '1',
      ['윤석열', '이재명', '심상정'],
      apiKey
    );

    console.log('✓ Fetched pledges for multiple candidates:');
    multiplePledges.forEach((result: any) => {
      if (result.success) {
        console.log(`  ✓ ${result.candidateName}: ${result.candidate?.name} (${result.candidate?.party})`);
      } else {
        console.log(`  ✗ ${result.candidateName}: ${result.error?.message}`);
      }
    });

  } catch (error: any) {
    console.error('\n✗ Test failed:', error.message);
    if (error.message.includes('Forbidden')) {
      console.log('\n💡 Tip: The API key might not be activated yet.');
      console.log('   Check data.go.kr portal and wait for activation (usually takes a few hours).');
    }
  } finally {
    await prisma.$disconnect();
  }

  console.log('\n=== Test Complete ===\n');
}

testNecApiChain().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
