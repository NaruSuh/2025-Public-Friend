import { BaseCrawler } from './baseCrawler';
import { CrawlerSiteConfig, CrawlOptions, CrawlResult, CrawledItem } from '@/types/crawler.types';
import { logger } from '@/config/logger';

// 사용자 정의 URL 크롤러
export class CustomCrawler extends BaseCrawler {
  constructor(config: Partial<CrawlerSiteConfig> = {}) {
    super({
      id: 'custom',
      name: 'Custom Crawler',
      baseUrl: '',
      selectors: {
        listItem: 'article, .item, .post, li',
        title: 'h1, h2, h3, .title',
        content: 'p, .content, .body',
        link: 'a',
      },
      ...config,
    });
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    let pagesProcessed = 0;

    if (!options.url) {
      this.addError('', 'URL is required for custom crawler');
      return this.buildResult(items, startTime, pagesProcessed);
    }

    try {
      logger.debug(`[Custom Crawler] Crawling: ${options.url}`);

      const html = await this.fetchWithPuppeteer(options.url);
      const $ = this.parseHtml(html);
      pagesProcessed++;

      // 자동 감지 또는 사용자 제공 셀렉터 사용
      const selectors = options.filters?.selectors || this.config.selectors;
      const listItems = $(selectors.listItem!);

      listItems.each((i, el) => {
        const item = $(el);
        const title = item.find(selectors.title!).first().text().trim();
        const content = item.find(selectors.content!).text().trim();
        const link = item.find(selectors.link!).attr('href');

        if (title || content) {
          items.push({
            id: `custom-${i}-${Date.now()}`,
            title: title || undefined,
            content: content || undefined,
            url: link ? this.resolveUrl(options.url!, link) : undefined,
            metadata: {
              sourceUrl: options.url,
            },
          });
        }
      });
    } catch (error: any) {
      this.addError(options.url, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed);
  }

  private resolveUrl(baseUrl: string, relativeUrl: string): string {
    if (relativeUrl.startsWith('http')) {
      return relativeUrl;
    }
    const base = new URL(baseUrl);
    return new URL(relativeUrl, base.origin).href;
  }
}
