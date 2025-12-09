import { BaseCrawler } from './baseCrawler';
import { NecLibraryCrawler } from './necLibraryCrawler';
import { NecPolicyCrawler } from './necPolicyCrawler';
import { PartyMinjooCrawler, PartyPPPCrawler } from './partyCrawler';
import { CustomCrawler } from './customCrawler';
import { CrawlerType } from '@/types/crawler.types';

export class CrawlerFactory {
  private static crawlers: Map<CrawlerType, () => BaseCrawler> = new Map<
    CrawlerType,
    () => BaseCrawler
  >([
    ['nec_library', () => new NecLibraryCrawler()],
    ['nec_policy', () => new NecPolicyCrawler()],
    ['party_minjoo', () => new PartyMinjooCrawler()],
    ['party_ppp', () => new PartyPPPCrawler()],
    ['custom', () => new CustomCrawler()],
  ]);

  static create(type: CrawlerType): BaseCrawler {
    const factory = this.crawlers.get(type);
    if (!factory) {
      // 미구현 크롤러에 대한 명확한 에러 메시지
      const unimplementedCrawlers = ['bigkinds', 'manifesto'];
      if (unimplementedCrawlers.includes(type.toLowerCase())) {
        throw new Error(
          `Crawler type '${type}' is not yet implemented. ` +
          `Currently available crawlers: ${Array.from(this.crawlers.keys()).join(', ')}`
        );
      }
      throw new Error(`Unknown crawler type: ${type}`);
    }
    return factory();
  }

  static register(type: CrawlerType, factory: () => BaseCrawler): void {
    this.crawlers.set(type, factory);
  }

  static getAvailableTypes(): CrawlerType[] {
    return Array.from(this.crawlers.keys());
  }

  static async getAvailableCrawlers(): Promise<CrawlerType[]> {
    const available: CrawlerType[] = [];

    for (const [type, factory] of this.crawlers) {
      const crawler = factory();
      // Check if crawler has isAvailable method
      if (typeof (crawler as any).isAvailable === 'function') {
        if (await (crawler as any).isAvailable()) {
          available.push(type);
        }
      } else {
        // If no isAvailable method, assume it's available
        available.push(type);
      }
    }

    return available;
  }

  static async isAvailable(type: CrawlerType): Promise<boolean> {
    const factory = this.crawlers.get(type);
    if (!factory) {
      return false;
    }

    const crawler = factory();
    // Check if crawler has isAvailable method
    if (typeof (crawler as any).isAvailable === 'function') {
      return await (crawler as any).isAvailable();
    }

    // If no isAvailable method, assume it's available
    return true;
  }
}
