import { BaseCrawler } from './baseCrawler';
import { CrawlerSiteConfig, CrawlOptions, CrawlResult, CrawledItem } from '@/types/crawler.types';
import path from 'path';
import { logger } from '@/config/logger';

const NEC_LIBRARY_CONFIG: CrawlerSiteConfig = {
  id: 'nec_library',
  name: '선거정보도서관',
  baseUrl: 'https://library.nec.go.kr',
  selectors: {
    listContainer: '.board-list',
    listItem: '.board-list tbody tr',
    title: '.title a',
    link: '.title a',
  },
  authentication: {
    type: 'none',
  },
};

export class NecLibraryCrawler extends BaseCrawler {
  constructor() {
    super(NEC_LIBRARY_CONFIG);
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      // 선거공보 검색 페이지 접근
      const searchUrl = this.buildSearchUrl(options);
      logger.debug(`[NEC Library] Crawling: ${searchUrl}`);

      const html = await this.fetchWithPuppeteer(searchUrl);
      const $ = this.parseHtml(html);
      pagesProcessed++;

      // 검색 결과 파싱
      const listItems = $(this.config.selectors.listItem!);

      for (let i = 0; i < listItems.length; i++) {
        const item = listItems.eq(i);

        try {
          const titleEl = item.find(this.config.selectors.title!);
          const title = titleEl.text().trim();
          const link = titleEl.attr('href');

          if (!title || !link) continue;

          const fullUrl = link.startsWith('http') ? link : `${this.config.baseUrl}${link}`;

          // 상세 페이지에서 PDF 링크 추출
          const detailHtml = await this.fetchWithPuppeteer(fullUrl);
          const $detail = this.parseHtml(detailHtml);

          const pdfLink = $detail('a[href*=".pdf"]').attr('href');

          const crawledItem: CrawledItem = {
            id: `nec-${i}-${Date.now()}`,
            title,
            url: fullUrl,
            fileUrl: pdfLink,
            category: this.extractCategory($detail),
            date: this.extractDate(item),
            metadata: {
              electionType: options.filters?.electionType,
              year: options.filters?.year,
            },
          };

          items.push(crawledItem);

          // PDF 다운로드 (옵션)
          if (options.downloadFiles && pdfLink && options.outputDir) {
            try {
              const filePath = await this.downloadFile(
                pdfLink.startsWith('http') ? pdfLink : `${this.config.baseUrl}${pdfLink}`,
                options.outputDir,
                `${crawledItem.id}.pdf`
              );
              downloadedFiles.push(filePath);
            } catch (downloadErr: any) {
              this.addError(pdfLink, `Download failed: ${downloadErr.message}`);
            }
          }

          // Rate limiting
          await new Promise((resolve) => setTimeout(resolve, 1000));
        } catch (itemErr: any) {
          this.addError(searchUrl, `Item parsing error: ${itemErr.message}`);
        }
      }
    } catch (error: any) {
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  private buildSearchUrl(options: CrawlOptions): string {
    // 선거정보도서관 검색 URL 구성
    const params = new URLSearchParams();

    if (options.filters?.year) {
      params.set('searchYear', options.filters.year.toString());
    }
    if (options.filters?.electionType) {
      params.set('searchElecType', options.filters.electionType);
    }

    return `${this.config.baseUrl}/neweps/3/1/paper.do?${params.toString()}`;
  }

  private extractCategory($: any): string | undefined {
    // 카테고리 추출 로직
    return $('meta[name="category"]').attr('content');
  }

  private extractDate(item: any): string | undefined {
    // 날짜 추출 로직
    const dateText = item.find('.date').text().trim();
    return dateText || undefined;
  }
}
