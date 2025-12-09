/**
 * 정당 웹사이트 크롤러
 *
 * 지원 정당:
 * - 더불어민주당 (theminjoo.kr)
 * - 국민의힘 (peoplepowerparty.kr)
 *
 * 크롤링 대상:
 * - 선거자료실
 * - 정책자료실
 * - 공약자료실
 * - PDF 정책공약집
 */

import { BaseCrawler } from './baseCrawler';
import {
  CrawlerSiteConfig,
  CrawlOptions,
  CrawlResult,
  CrawledItem,
} from '@/types/crawler.types';
import { logger } from '@/config/logger';

// 더불어민주당 설정
const MINJOO_CONFIG: CrawlerSiteConfig = {
  id: 'party_minjoo',
  name: '더불어민주당',
  baseUrl: 'https://theminjoo.kr',
  selectors: {
    listContainer: '.board-list, table tbody',
    listItem: 'tr, .list-item',
    title: '.title a, td.title a',
    link: '.title a, td.title a',
    pdfLink: 'a[href$=".pdf"]',
  },
  authentication: { type: 'none' },
};

// 국민의힘 설정
const PPP_CONFIG: CrawlerSiteConfig = {
  id: 'party_ppp',
  name: '국민의힘',
  baseUrl: 'https://www.peoplepowerparty.kr',
  selectors: {
    listContainer: '.board-list, .list-wrap',
    listItem: 'li, tr',
    title: '.title a, .tit a',
    link: '.title a, .tit a',
    pdfLink: 'a[href$=".pdf"], a[href*="download"]',
  },
  authentication: { type: 'none' },
};

// 게시판 ID 매핑
const BOARD_IDS = {
  minjoo: {
    election: 16, // 선거자료실
    policy: 15, // 정책자료실
    press: 1, // 보도자료
  },
  ppp: {
    policy: 'mainPolicyView',
    pledge: 'data_pledge',
  },
};

// 크롤링 설정 상수
const CRAWL_SETTINGS = {
  CONTENT_PREVIEW_LENGTH: 500,
  FILENAME_MAX_LENGTH: 30,
  DEFAULT_START_PAGE: 1,
  DEFAULT_END_PAGE: 3,
  REQUEST_DELAY_MS: 1000,
  DETAIL_PAGE_DELAY_MS: 500,
} as const;

export class PartyMinjooCrawler extends BaseCrawler {
  constructor() {
    super(MINJOO_CONFIG);
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      logger.info('[Minjoo] Starting crawl...');

      // 1. 선거자료실 크롤링
      const electionItems = await this.crawlBoard(
        BOARD_IDS.minjoo.election,
        '선거자료실',
        options
      );
      items.push(...electionItems);
      pagesProcessed++;

      // 2. 정책자료실 크롤링 (옵션)
      if (options.filters?.includePolicy) {
        const policyItems = await this.crawlBoard(
          BOARD_IDS.minjoo.policy,
          '정책자료실',
          options
        );
        items.push(...policyItems);
        pagesProcessed++;
      }

      // 3. PDF 다운로드
      if (options.downloadFiles && options.outputDir) {
        for (const item of items) {
          if (item.fileUrl) {
            try {
              const filePath = await this.downloadFile(
                item.fileUrl,
                options.outputDir,
                this.generateFileName(item)
              );
              downloadedFiles.push(filePath);
            } catch (err: any) {
              this.addError(item.fileUrl, `Download failed: ${err.message}`);
            }
          }
        }
      }

      logger.info(`[Minjoo] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      logger.error(`[Minjoo] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  /**
   * 게시판 크롤링
   */
  private async crawlBoard(
    boardId: number,
    boardName: string,
    options: CrawlOptions
  ): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const startPage = options.startPage || CRAWL_SETTINGS.DEFAULT_START_PAGE;
    const endPage = options.endPage || CRAWL_SETTINGS.DEFAULT_END_PAGE;

    for (let page = startPage; page <= endPage; page++) {
      const url = `${this.config.baseUrl}/main/sub/news/list.php?brd=${boardId}&page=${page}`;
      logger.debug(`[Minjoo] Crawling ${boardName} page ${page}: ${url}`);

      try {
        const html = await this.fetchPage(url);
        const $ = this.parseHtml(html);

        $(this.config.selectors.listItem!).each((i, row) => {
          const $row = $(row);
          const titleEl = $row.find(this.config.selectors.title!);
          const title = titleEl.text().trim();
          const link = titleEl.attr('href');

          if (!title || title === '제목') return; // 헤더 제외

          const fullUrl = link
            ? link.startsWith('http')
              ? link
              : `${this.config.baseUrl}${link}`
            : url;

          const dateText = $row.find('.date, td:nth-child(3)').text().trim();

          items.push({
            id: `minjoo-${boardId}-${page}-${i}-${Date.now()}`,
            title,
            url: fullUrl,
            category: boardName,
            date: this.parseDate(dateText),
            metadata: {
              partyName: '더불어민주당',
              boardId,
              boardName,
              sourceSite: 'party_minjoo',
            },
          });
        });

        // Rate limiting
        await this.delay(CRAWL_SETTINGS.REQUEST_DELAY_MS);
      } catch (error: any) {
        this.addError(url, error.message);
      }
    }

    // 상세 페이지에서 PDF 링크 추출
    for (const item of items) {
      if (item.url && item.url !== this.config.baseUrl) {
        try {
          const detailHtml = await this.fetchPage(item.url);
          const $detail = this.parseHtml(detailHtml);

          // PDF 링크 찾기
          const pdfLink = $detail('a[href$=".pdf"]').first().attr('href');
          if (pdfLink) {
            item.fileUrl = pdfLink.startsWith('http')
              ? pdfLink
              : `${this.config.baseUrl}${pdfLink}`;
          }

          // 본문 내용 추출
          const content = $detail('.post-content, .view-content, .board-view')
            .text()
            .trim();
          if (content) {
            item.content = content.substring(0, CRAWL_SETTINGS.CONTENT_PREVIEW_LENGTH);
          }

          await this.delay(CRAWL_SETTINGS.DETAIL_PAGE_DELAY_MS);
        } catch {
          // 상세 페이지 접근 실패는 무시
        }
      }
    }

    return items;
  }

  private generateFileName(item: CrawledItem): string {
    const date = new Date().toISOString().split('T')[0];
    const safeTitle = (item.title || 'unknown')
      .substring(0, CRAWL_SETTINGS.FILENAME_MAX_LENGTH)
      .replace(/[^a-zA-Z0-9가-힣]/g, '_');
    return `minjoo_${safeTitle}_${date}.pdf`;
  }

  private parseDate(dateText: string): string | undefined {
    // 2024.03.25 or 2024-03-25 형식 처리
    const match = dateText.match(/(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})/);
    if (match && match[1] && match[2] && match[3]) {
      const year = match[1];
      const month = match[2];
      const day = match[3];
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    return undefined;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await this.fetchPage(this.config.baseUrl);
      return response.includes('더불어민주당') || response.includes('theminjoo');
    } catch {
      return false;
    }
  }
}

export class PartyPPPCrawler extends BaseCrawler {
  constructor() {
    super(PPP_CONFIG);
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      logger.info('[PPP] Starting crawl...');

      // 1. 정책자료실 크롤링
      const policyItems = await this.crawlPolicyPage(options);
      items.push(...policyItems);
      pagesProcessed++;

      // 2. 공약자료실 크롤링 (불안정할 수 있음)
      try {
        const pledgeItems = await this.crawlPledgePage(options);
        items.push(...pledgeItems);
        pagesProcessed++;
      } catch (err: any) {
        logger.warn(`[PPP] Pledge page unavailable: ${err.message}`);
      }

      // 3. PDF 다운로드
      if (options.downloadFiles && options.outputDir) {
        for (const item of items) {
          if (item.fileUrl) {
            try {
              const filePath = await this.downloadFile(
                item.fileUrl,
                options.outputDir,
                this.generateFileName(item)
              );
              downloadedFiles.push(filePath);
            } catch (err: any) {
              this.addError(item.fileUrl, `Download failed: ${err.message}`);
            }
          }
        }
      }

      logger.info(`[PPP] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      logger.error(`[PPP] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  /**
   * 정책자료실 크롤링
   */
  private async crawlPolicyPage(options: CrawlOptions): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/web/policy/policy/mainPolicyView.do`;

    logger.debug(`[PPP] Crawling policy page: ${url}`);

    try {
      // 세션 유지를 위해 Puppeteer 사용
      const html = await this.fetchWithPuppeteer(url);
      const $ = this.parseHtml(html);

      // 정책 항목 파싱
      $('.policy-item, .list-item, li').each((i, el) => {
        const $el = $(el);
        const title = $el.find('.title, .tit, a').first().text().trim();
        const link = $el.find('a').first().attr('href');

        if (!title) return;

        const fullUrl = link
          ? link.startsWith('http')
            ? link
            : `${this.config.baseUrl}${link}`
          : url;

        items.push({
          id: `ppp-policy-${i}-${Date.now()}`,
          title,
          url: fullUrl,
          category: '정책자료실',
          metadata: {
            partyName: '국민의힘',
            sourceSite: 'party_ppp',
          },
        });
      });

      // PDF 링크 직접 추출
      $('a[href$=".pdf"], a[href*="download"]').each((i, el) => {
        const $el = $(el);
        const href = $el.attr('href');
        const text = $el.text().trim() || `PDF 문서 ${i + 1}`;

        if (href && !items.some((item) => item.fileUrl === href)) {
          items.push({
            id: `ppp-pdf-${i}-${Date.now()}`,
            title: text,
            url,
            fileUrl: href.startsWith('http') ? href : `${this.config.baseUrl}${href}`,
            category: 'PDF',
            metadata: {
              partyName: '국민의힘',
              sourceSite: 'party_ppp',
            },
          });
        }
      });
    } catch (error: any) {
      this.addError(url, error.message);
    }

    return items;
  }

  /**
   * 공약자료실 크롤링
   */
  private async crawlPledgePage(options: CrawlOptions): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/renewal/policy/data_pledge.do`;

    logger.debug(`[PPP] Crawling pledge page: ${url}`);

    try {
      const html = await this.fetchWithPuppeteer(url);
      const $ = this.parseHtml(html);

      // 공약 항목 파싱
      $('.pledge-item, .list-item, tr').each((i, el) => {
        const $el = $(el);
        const title = $el.find('.title, .tit, td').first().text().trim();
        const pdfLink = $el.find('a[href$=".pdf"]').attr('href');

        if (!title) return;

        items.push({
          id: `ppp-pledge-${i}-${Date.now()}`,
          title,
          url,
          fileUrl: pdfLink
            ? pdfLink.startsWith('http')
              ? pdfLink
              : `${this.config.baseUrl}${pdfLink}`
            : undefined,
          category: '공약자료실',
          metadata: {
            partyName: '국민의힘',
            sourceSite: 'party_ppp',
          },
        });
      });
    } catch (error: any) {
      // 공약자료실은 불안정할 수 있음
      logger.warn(`[PPP] Pledge page error: ${error.message}`);
    }

    return items;
  }

  private generateFileName(item: CrawledItem): string {
    const date = new Date().toISOString().split('T')[0];
    const safeTitle = (item.title || 'unknown')
      .substring(0, CRAWL_SETTINGS.FILENAME_MAX_LENGTH)
      .replace(/[^a-zA-Z0-9가-힣]/g, '_');
    return `ppp_${safeTitle}_${date}.pdf`;
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await this.fetchPage(this.config.baseUrl);
      return response.includes('국민의힘') || response.includes('peoplepowerparty');
    } catch {
      return false;
    }
  }
}
