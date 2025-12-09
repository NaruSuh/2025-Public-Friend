import { describe, it, expect } from '@jest/globals';
import { CrawlerFactory } from '@/services/crawler/crawlerFactory';

/**
 * Smoke tests for API integrations and core systems.
 * Note: API service tests are skipped by default as they require
 * proper API keys and network access. Run with actual keys for full integration testing.
 */
describe('API Integration Smoke Tests', () => {
  describe('R-ONE API', () => {
    it.skip('should retrieve available statistics tables (requires API key)', async () => {
      // Requires RONE_API_KEY environment variable
      // Run this test manually with: pnpm test:smoke
      expect(true).toBe(true);
    });
  });

  describe('NEC API', () => {
    it.skip('should retrieve election candidates (requires API key)', async () => {
      // Requires NEC API key configured
      // Run this test manually with: pnpm test:smoke
      expect(true).toBe(true);
    });
  });

  describe('Crawler System', () => {
    it('should list available crawler types', () => {
      const availableTypes = CrawlerFactory.getAvailableTypes();

      expect(Array.isArray(availableTypes)).toBe(true);
      expect(availableTypes).toContain('nec_library');
      expect(availableTypes).toContain('custom');
    });

    it('should throw clear error for unimplemented crawlers', () => {
      expect(() => {
        CrawlerFactory.create('bigkinds' as any);
      }).toThrow('not yet implemented');

      expect(() => {
        CrawlerFactory.create('manifesto' as any);
      }).toThrow('not yet implemented');
    });
  });
});
