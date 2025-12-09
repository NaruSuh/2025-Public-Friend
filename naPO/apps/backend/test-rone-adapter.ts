import { ROneAdapter } from './src/services/api/adapters/roneAdapter';
import { QueryFilters } from './src/types/nlp.types';

console.log('=== R-ONE Adapter Test ===\n');

// Test 1: Basic filter conversion
console.log('Test 1: Basic filter with region and date');
const filters1: QueryFilters = {
  region: '서울',
  dateRange: {
    start: '2024-01-01',
    end: '2024-12-31',
  },
};

const params1 = ROneAdapter.adaptFilters(filters1);
console.log('Input:', JSON.stringify(filters1, null, 2));
console.log('Output:', JSON.stringify(params1, null, 2));
console.log('Validation:', ROneAdapter.validateParams(params1));
console.log('');

// Test 2: No date range (should use default)
console.log('Test 2: No date range');
const filters2: QueryFilters = {
  region: '부산',
};

const params2 = ROneAdapter.adaptFilters(filters2);
console.log('Input:', JSON.stringify(filters2, null, 2));
console.log('Output:', JSON.stringify(params2, null, 2));
console.log('Validation:', ROneAdapter.validateParams(params2));
console.log('');

// Test 3: Empty filters
console.log('Test 3: Empty filters');
const filters3: QueryFilters = {};

const params3 = ROneAdapter.adaptFilters(filters3);
console.log('Input:', JSON.stringify(filters3, null, 2));
console.log('Output:', JSON.stringify(params3, null, 2));
console.log('Validation:', ROneAdapter.validateParams(params3));
console.log('');

// Test 4: Response normalization (mock data)
console.log('Test 4: Response normalization');
const mockResponse = {
  head: {
    list_total_count: 100,
    RESULT: {
      CODE: 'INFO-000',
      MESSAGE: '정상 처리되었습니다.',
    },
  },
  row: [
    { CLS_NM: '서울', ITM_NM: '지수', DTA_VAL: 100.5 },
    { CLS_NM: '부산', ITM_NM: '지수', DTA_VAL: 95.2 },
  ],
};

const normalized = ROneAdapter.normalizeResponse(mockResponse, params1);
console.log('Normalized:', JSON.stringify(normalized, null, 2));
console.log('');

console.log('=== All Tests Complete ===');
