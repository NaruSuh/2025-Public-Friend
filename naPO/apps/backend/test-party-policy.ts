import { PrismaClient } from '@prisma/client';
import { PartyPolicyService } from './src/services/api/partyPolicyService';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function testPartyPolicy() {
  console.log('\n=== Testing Party Policy API ===\n');

  try {
    // Get API key from environment
    const apiKey = process.env.NEC_CANDIDATE_API_KEY || process.env.NEC_MANIFESTO_API_KEY;
    if (!apiKey) {
      throw new Error('NEC API key not found in .env');
    }

    console.log('API Key loaded:', apiKey.substring(0, 10) + '...');

    const electionId = '20220309'; // 2022 대통령선거
    const mainParties = ['국민의힘', '더불어민주당', '정의당'];

    // ============================================
    // Test 1: Get party policy for 국민의힘
    // ============================================
    console.log('\n[Test 1] Fetching party policy for 국민의힘...');
    const ppp = await PartyPolicyService.getPartyPolicy(apiKey, electionId, '국민의힘');

    if (ppp.success) {
      console.log('✓ Party policy retrieved successfully');
      if (ppp.data && ppp.data.length > 0) {
        const policy = ppp.data[0];
        console.log(`  - Party: ${policy.partyName}`);
        console.log(`  - Policy Count: ${policy.policyCount}`);
        console.log(`  - Policies Found: ${policy.policies.length}`);
        console.log('\n  First 3 policies:');
        policy.policies.slice(0, 3).forEach((p: any, i: number) => {
          console.log(`    ${i + 1}. [${p.realm || 'N/A'}] ${p.title}`);
        });
      }
    } else {
      console.error('✗ Failed to fetch party policy:', ppp.error);
    }

    // ============================================
    // Test 2: Get policies for multiple parties
    // ============================================
    console.log('\n[Test 2] Fetching policies for multiple parties...');
    const multiPolicies = await PartyPolicyService.getMultiplePartyPolicies(
      apiKey,
      electionId,
      mainParties
    );

    console.log('✓ Multiple party policies retrieved');
    multiPolicies.forEach((result: any) => {
      if (result.success && result.data && result.data.length > 0) {
        const policy = result.data[0];
        console.log(`  ✓ ${policy.partyName}: ${policy.policyCount} policies`);
      } else {
        console.log(`  ✗ ${result.partyName}: ${result.error?.message || 'No data'}`);
      }
    });

    // ============================================
    // Test 3: Compare party policies
    // ============================================
    console.log('\n[Test 3] Comparing party policies...');
    const comparison = await PartyPolicyService.comparePartyPolicies(
      apiKey,
      electionId,
      mainParties
    );

    if (comparison.success) {
      console.log('✓ Party policy comparison completed');
      console.log(`  - Parties analyzed: ${comparison.comparison.parties.length}`);
      console.log(`  - Policy realms found: ${comparison.comparison.realms.length}`);
      console.log('\n  Policy realms:');
      comparison.comparison.realms.slice(0, 5).forEach((realm: string, i: number) => {
        console.log(`    ${i + 1}. ${realm}`);
      });
    } else {
      console.error('✗ Failed to compare policies:', comparison.error);
    }

    // ============================================
    // Test 4: Compare policies by realm (노동)
    // ============================================
    console.log('\n[Test 4] Comparing policies in realm: 노동...');
    const laborPolicies = await PartyPolicyService.compareByRealm(
      apiKey,
      electionId,
      mainParties,
      '노동'
    );

    if (laborPolicies.success) {
      console.log('✓ Labor policy comparison completed');
      Object.entries(laborPolicies.policies).forEach(([party, policies]: [string, any]) => {
        console.log(`  - ${party}: ${policies.length} labor-related policies`);
        if (policies.length > 0) {
          console.log(`    Example: ${policies[0].title}`);
        }
      });
    } else {
      console.error('✗ Failed to compare labor policies');
    }

    // ============================================
    // Test 5: Search party policies by keyword
    // ============================================
    console.log('\n[Test 5] Searching for "일자리" in 국민의힘 policies...');
    const searchResult = await PartyPolicyService.searchPartyPolicies(
      apiKey,
      electionId,
      '국민의힘',
      '일자리'
    );

    if (searchResult.success) {
      console.log('✓ Search completed');
      console.log(`  - Total policies: ${searchResult.totalPolicies}`);
      console.log(`  - Matched policies: ${searchResult.matchedCount}`);
      if (searchResult.policies.length > 0) {
        console.log('\n  Matched policies:');
        searchResult.policies.slice(0, 3).forEach((p: any, i: number) => {
          console.log(`    ${i + 1}. [${p.realm || 'N/A'}] ${p.title}`);
        });
      }
    } else {
      console.error('✗ Search failed:', searchResult.error);
    }

    // ============================================
    // Test 6: Get party policy stats
    // ============================================
    console.log('\n[Test 6] Getting policy stats for 국민의힘...');
    const stats = await PartyPolicyService.getPartyPolicyStats(apiKey, electionId, '국민의힘');

    if (stats.success) {
      console.log('✓ Policy stats retrieved');
      console.log(`  - Party: ${stats.stats.partyName}`);
      console.log(`  - Total policies: ${stats.stats.totalPolicies}`);
      console.log(`  - Policies with content: ${stats.stats.hasContent}`);
      console.log(`  - Policies without content: ${stats.stats.noContent}`);
      console.log('\n  Policies by realm:');
      Object.entries(stats.stats.realmCounts).forEach(([realm, count]: [string, any]) => {
        console.log(`    - ${realm}: ${count}`);
      });
    } else {
      console.error('✗ Failed to get stats:', stats.error);
    }

    // ============================================
    // Test 7: Compare policy stats for multiple parties
    // ============================================
    console.log('\n[Test 7] Comparing policy stats for multiple parties...');
    const statsComparison = await PartyPolicyService.comparePartyPolicyStats(
      apiKey,
      electionId,
      mainParties
    );

    if (statsComparison.success) {
      console.log('✓ Policy stats comparison completed');
      console.log(`  - Parties analyzed: ${statsComparison.partiesCount}`);
      statsComparison.stats.forEach((stat: any) => {
        console.log(`\n  ${stat.partyName}:`);
        console.log(`    - Total: ${stat.totalPolicies}`);
        console.log(`    - With content: ${stat.hasContent}`);
        console.log(`    - Realms: ${Object.keys(stat.realmCounts).length}`);
      });
    } else {
      console.error('✗ Failed to compare stats');
    }

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

testPartyPolicy().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
