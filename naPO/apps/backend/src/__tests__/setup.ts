// Jest setup file for backend tests
import { beforeAll, afterAll, afterEach } from '@jest/globals';

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.DATABASE_URL =
  process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/napo_test';
process.env.JWT_SECRET = 'test-jwt-secret-key-for-testing-only';
process.env.PORT = '3999'; // Use different port for tests

// Global test timeout
jest.setTimeout(10000);

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});

// Optional: Add global beforeAll/afterAll if needed
beforeAll(async () => {
  // Initialize test database, mocks, etc.
  console.log('🧪 Test environment initialized');
});

afterAll(async () => {
  // Clean up test database, close connections, etc.
  console.log('🧪 Test environment cleaned up');
});
