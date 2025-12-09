import { PrismaClient } from '@prisma/client';
import { NecManifestoAdapter } from './src/services/api/adapters/necManifestoAdapter';
import { QueryFilters } from './src/types/nlp.types';

const prisma = new PrismaClient();

async function testNecManifestoAdapter() {
  console.log('\n=== Testing NEC Manifesto Adapter ===\n');

  // Test 1: Check if API source exists in database
  console.log('1. Checking API source in database...');
  const apiSource = await prisma.apiSource.findFirst({
    where: { name: 'public_data_election' },
  });

  if (apiSource) {
    console.log('✓ API source found:', apiSource.name);
    console.log('  - ID:', apiSource.id);
    console.log('  - Display Name:', apiSource.displayName);
  } else {
    console.log('✗ API source NOT found in database');
    console.log('  Expected name: "public_data_election"');
  }

  // Test 2: Check if API key exists
  console.log('\n2. Checking API key in database...');
  if (apiSource) {
    const apiKey = await prisma.apiKey.findFirst({
      where: {
        sourceId: apiSource.id,
        isActive: true,
      },
    });

    if (apiKey) {
      console.log('✓ API key found');
      console.log('  - Key preview:', apiKey.keyValue.substring(0, 10) + '...');
      console.log('  - Is active:', apiKey.isActive);
      console.log('  - Expires at:', apiKey.expiresAt || 'Never');
    } else {
      console.log('✗ API key NOT found');
    }
  }

  // Test 3: Filter adaptation
  console.log('\n3. Testing filter adaptation...');
  const testFilters: QueryFilters = {
    dateRange: {
      start: '2022-03-09',
      end: '2022-03-09',
    },
    election: {
      type: '대통령선거',
    },
    custom: {
      cnddtId: '1',
    },
    limit: 10,
  };

  console.log('Input filters:', JSON.stringify(testFilters, null, 2));
  const adaptedParams = NecManifestoAdapter.adaptFilters(testFilters);
  console.log('Adapted params:', JSON.stringify(adaptedParams, null, 2));

  // Test 4: Parameter validation
  console.log('\n4. Testing parameter validation...');
  const validation = NecManifestoAdapter.validateParams(adaptedParams);
  if (validation.valid) {
    console.log('✓ Parameters are valid');
  } else {
    console.log('✗ Validation errors:');
    validation.errors.forEach((err) => console.log('  -', err));
  }

  // Test 5: Response normalization with mock data
  console.log('\n5. Testing response normalization...');
  const mockApiResponse = {
    response: {
      header: {
        resultCode: '00',
        resultMsg: 'NORMAL SERVICE',
      },
      body: {
        totalCount: 1,
        pageNo: 1,
        numOfRows: 10,
        items: {
          item: {
            sgId: '20220309',
            sgTypecode: '1',
            cnddtId: '1',
            sggName: '전국',
            sidoName: '',
            wiwName: '',
            partyName: '국민의힘',
            krName: '윤석열',
            cnName: '尹錫悅',
            prmsCnt: '3',
            prmsOrd1: '1',
            prmsRealmName1: '경제',
            prmsTitle1: '일자리 창출',
            prmsCont1: '민간 주도 일자리 100만개 창출',
            prmsOrd2: '2',
            prmsRealmName2: '부동산',
            prmsTitle2: '주거 안정',
            prmsCont2: '250만호 공급',
            prmsOrd3: '3',
            prmsRealmName3: '교육',
            prmsTitle3: '교육 혁신',
            prmsCont3: '공정한 교육 기회 제공',
          },
        },
      },
    },
  };

  const normalized = NecManifestoAdapter.normalizeResponse(mockApiResponse);
  console.log('Normalized response:', JSON.stringify(normalized, null, 2));

  // Test 6: Test without cnddtId (should fail validation)
  console.log('\n6. Testing validation failure (missing cnddtId)...');
  const invalidFilters: QueryFilters = {
    dateRange: {
      start: '2022-03-09',
    },
    election: {
      type: '대통령',
    },
    limit: 10,
  };

  const invalidParams = NecManifestoAdapter.adaptFilters(invalidFilters);
  const invalidValidation = NecManifestoAdapter.validateParams(invalidParams);
  if (!invalidValidation.valid) {
    console.log('✓ Correctly detected invalid parameters:');
    invalidValidation.errors.forEach((err) => console.log('  -', err));
  } else {
    console.log('✗ Should have failed validation');
  }

  // Test 7: Election type mapping
  console.log('\n7. Testing election type mapping...');
  const electionTypes = [
    { input: '대통령선거', expected: '1' },
    { input: '시도지사선거', expected: '3' },
    { input: '구시군의장선거', expected: '4' },
    { input: '교육감선거', expected: '11' },
  ];

  electionTypes.forEach(({ input, expected }) => {
    const filters: QueryFilters = {
      dateRange: { start: '2022-03-09' },
      election: { type: input },
      custom: { cnddtId: '1' },
    };
    const params = NecManifestoAdapter.adaptFilters(filters);
    const match = params.sgTypecode === expected;
    console.log(`  ${match ? '✓' : '✗'} ${input} → ${params.sgTypecode} (expected: ${expected})`);
  });

  await prisma.$disconnect();
  console.log('\n=== Test Complete ===\n');
}

testNecManifestoAdapter().catch((error) => {
  console.error('Test failed:', error);
  process.exit(1);
});
