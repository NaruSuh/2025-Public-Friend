import { PrismaClient } from '@prisma/client';
import { CommonCodeService } from './src/services/api/commonCodeService';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function testCommonCode() {
  console.log('\n=== Testing NEC Common Code API ===\n');

  try {
    // Get API key from environment
    const apiKey = process.env.NEC_CANDIDATE_API_KEY || process.env.NEC_MANIFESTO_API_KEY;
    if (!apiKey) {
      throw new Error('NEC API key not found in .env');
    }

    console.log('API Key loaded:', apiKey.substring(0, 10) + '...');

    // ============================================
    // Test 1: Get all election codes
    // ============================================
    console.log('\n[Test 1] Fetching all election codes...');
    const electionCodes = await CommonCodeService.getElectionCodes(apiKey);

    if (electionCodes.success) {
      console.log(`✓ Found ${electionCodes.totalCount} election codes`);
      console.log('\nRecent elections:');
      electionCodes.data.slice(0, 5).forEach((election: any, index: number) => {
        console.log(`  ${index + 1}. ${election.electionName} (${election.electionId})`);
        console.log(`     - Type: ${election.electionTypeCode}`);
        console.log(`     - Date: ${election.voteDate}`);
      });
    } else {
      console.error('✗ Failed to fetch election codes:', electionCodes.error);
    }

    // ============================================
    // Test 2: Search for specific elections
    // ============================================
    console.log('\n[Test 2] Searching for "대통령" elections...');
    const presidentialElections = await CommonCodeService.searchElections(apiKey, '대통령');

    if (presidentialElections.length > 0) {
      console.log(`✓ Found ${presidentialElections.length} presidential elections`);
      presidentialElections.slice(0, 3).forEach((election: any, index: number) => {
        console.log(`  ${index + 1}. ${election.electionName} (${election.electionId})`);
      });
    } else {
      console.log('✗ No presidential elections found');
    }

    // ============================================
    // Test 3: Get party codes for 2022 presidential election
    // ============================================
    console.log('\n[Test 3] Fetching party codes for 2022 presidential election...');
    const partyCodes = await CommonCodeService.getPartyCodes(apiKey, '20220309', '1');

    if (partyCodes.success) {
      console.log(`✓ Found ${partyCodes.totalCount} parties`);
      console.log('\nParty list:');
      partyCodes.data.slice(0, 10).forEach((party: any, index: number) => {
        console.log(`  ${index + 1}. ${party.partyName} (순서: ${party.order})`);
      });
    } else {
      console.error('✗ Failed to fetch party codes:', partyCodes.error);
    }

    // ============================================
    // Test 4: Get district codes
    // ============================================
    console.log('\n[Test 4] Fetching district codes...');
    const districtCodes = await CommonCodeService.getDistrictCodes(apiKey);

    if (districtCodes.success) {
      console.log(`✓ Found ${districtCodes.totalCount} districts`);
      console.log('\nSample districts:');
      districtCodes.data.slice(0, 5).forEach((district: any, index: number) => {
        console.log(`  ${index + 1}. ${district.districtName} (${district.provinceName})`);
      });
    } else {
      console.error('✗ Failed to fetch district codes:', districtCodes.error);
    }

    // ============================================
    // Test 5: Search districts by province
    // ============================================
    console.log('\n[Test 5] Fetching districts in 서울특별시...');
    const seoulDistricts = await CommonCodeService.getDistrictsByProvince(apiKey, '서울특별시');

    if (seoulDistricts.length > 0) {
      console.log(`✓ Found ${seoulDistricts.length} districts in Seoul`);
      seoulDistricts.slice(0, 5).forEach((district: any, index: number) => {
        console.log(`  ${index + 1}. ${district.districtName}`);
      });
    } else {
      console.log('✗ No districts found in Seoul');
    }

    // ============================================
    // Test 6: Get constituency codes for 2024 national assembly election
    // ============================================
    console.log('\n[Test 6] Fetching constituency codes for 2024 national assembly election...');
    const constituencyCodes = await CommonCodeService.getConstituencyCodes(
      apiKey,
      '20240410',
      '2'
    );

    if (constituencyCodes.success) {
      console.log(`✓ Found ${constituencyCodes.totalCount} constituencies`);
      console.log('\nSample constituencies:');
      constituencyCodes.data.slice(0, 5).forEach((constituency: any, index: number) => {
        console.log(
          `  ${index + 1}. ${constituency.constituencyName} (${constituency.provinceName})`
        );
        console.log(`     - District: ${constituency.districtName}`);
        console.log(`     - Seats: ${constituency.seatCount}`);
      });
    } else {
      console.error('✗ Failed to fetch constituency codes:', constituencyCodes.error);
    }

    // ============================================
    // Test 7: Get job codes
    // ============================================
    console.log('\n[Test 7] Fetching job codes...');
    const jobCodes = await CommonCodeService.getJobCodes(apiKey);

    if (jobCodes.success) {
      console.log(`✓ Found ${jobCodes.totalCount} job codes`);
      console.log('\nSample jobs:');
      jobCodes.data.slice(0, 10).forEach((job: any, index: number) => {
        console.log(`  ${index + 1}. ${job.jobName} (ID: ${job.jobId})`);
      });
    } else {
      console.error('✗ Failed to fetch job codes:', jobCodes.error);
    }

    // ============================================
    // Test 8: Get education codes
    // ============================================
    console.log('\n[Test 8] Fetching education codes...');
    const educationCodes = await CommonCodeService.getEducationCodes(apiKey);

    if (educationCodes.success) {
      console.log(`✓ Found ${educationCodes.totalCount} education codes`);
      console.log('\nEducation levels:');
      educationCodes.data.forEach((education: any, index: number) => {
        console.log(`  ${index + 1}. ${education.educationName} (ID: ${education.educationId})`);
      });
    } else {
      console.error('✗ Failed to fetch education codes:', educationCodes.error);
    }

    // ============================================
    // Test 9: Get election info by ID
    // ============================================
    console.log('\n[Test 9] Getting info for election 20220309...');
    const electionInfo = await CommonCodeService.getElectionInfo(apiKey, '20220309');

    if (electionInfo) {
      console.log('✓ Election info found:');
      console.log(`  - Name: ${electionInfo.electionName}`);
      console.log(`  - ID: ${electionInfo.electionId}`);
      console.log(`  - Type: ${electionInfo.electionTypeCode}`);
      console.log(`  - Date: ${electionInfo.voteDate}`);
    } else {
      console.log('✗ Election not found');
    }

    // ============================================
    // Test 10: Search parties by keyword
    // ============================================
    console.log('\n[Test 10] Searching for parties with "민주"...');
    const democraticParties = await CommonCodeService.searchParties(
      apiKey,
      '20220309',
      '1',
      '민주'
    );

    if (democraticParties.length > 0) {
      console.log(`✓ Found ${democraticParties.length} parties with "민주"`);
      democraticParties.forEach((party: any, index: number) => {
        console.log(`  ${index + 1}. ${party.partyName}`);
      });
    } else {
      console.log('✗ No parties found with "민주"');
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

testCommonCode().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
