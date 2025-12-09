#!/usr/bin/env node
/**
 * Standalone 크롤러 스크립트 (path alias 없이)
 *
 * 사용법:
 *   npx tsx src/scripts/standaloneCrawler.ts [options]
 *
 * 옵션:
 *   --crawler=<type>   특정 크롤러만 실행 (nec_policy, party_minjoo, party_ppp)
 *   --download         PDF 다운로드 활성화
 *   --pages=<n>        크롤링할 페이지 수 (기본: 3)
 */

import puppeteer, { Browser } from 'puppeteer';
import * as cheerio from 'cheerio';
import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';

// ============ Types ============
interface CrawledItem {
  id: string;
  title: string;
  url: string;
  content?: string;
  date?: string;
  fileUrl?: string;
  category?: string;
  metadata?: Record<string, any>;
}

interface CrawlResult {
  success: boolean;
  crawlerId: string;
  itemCount: number;
  items: CrawledItem[];
  downloadedFiles?: string[];
  errors?: { url: string; message: string; timestamp: string }[];
  metadata: {
    startTime: string;
    endTime: string;
    durationMs: number;
    pagesProcessed: number;
  };
}

interface CrawlOptions {
  startPage?: number;
  endPage?: number;
  downloadFiles?: boolean;
  outputDir?: string;
  filters?: {
    includePolicy?: boolean;
    includeCandidates?: boolean;
    partyName?: string;
  };
}

// ============ Settings ============
const CRAWL_SETTINGS = {
  CONTENT_PREVIEW_LENGTH: 500,
  FILENAME_MAX_LENGTH: 30,
  DEFAULT_START_PAGE: 1,
  DEFAULT_END_PAGE: 3,
  REQUEST_DELAY_MS: 1000,
  DETAIL_PAGE_DELAY_MS: 500,
} as const;

const BASE_OUTPUT_DIR = path.resolve(__dirname, '../../../data/crawled');

// ============ Base Crawler ============
abstract class BaseCrawler {
  protected browser: Browser | null = null;
  protected errors: { url: string; message: string; timestamp: string }[] = [];
  protected config: { id: string; name: string; baseUrl: string };

  constructor(config: { id: string; name: string; baseUrl: string }) {
    this.config = config;
  }

  abstract crawl(options: CrawlOptions): Promise<CrawlResult>;

  protected async initBrowser(): Promise<Browser> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
      });
    }
    return this.browser;
  }

  protected async closeBrowser(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  protected async fetchPage(url: string): Promise<string> {
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
      },
      timeout: 30000,
    });
    return response.data;
  }

  protected async fetchWithPuppeteer(url: string): Promise<string> {
    const browser = await this.initBrowser();
    const page = await browser.newPage();

    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

    const content = await page.content();
    await page.close();

    return content;
  }

  protected parseHtml(html: string): cheerio.CheerioAPI {
    return cheerio.load(html);
  }

  protected async downloadFile(url: string, outputDir: string, fileName?: string): Promise<string> {
    const response = await axios.get(url, {
      responseType: 'arraybuffer',
      timeout: 60000,
    });

    const finalFileName = fileName || path.basename(url);
    const filePath = path.join(outputDir, finalFileName);

    await fs.mkdir(outputDir, { recursive: true });
    await fs.writeFile(filePath, response.data);

    return filePath;
  }

  protected addError(url: string, message: string): void {
    this.errors.push({
      url,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  protected buildResult(
    items: CrawledItem[],
    startTime: Date,
    pagesProcessed: number,
    downloadedFiles?: string[]
  ): CrawlResult {
    return {
      success: items.length > 0 || this.errors.length === 0,
      crawlerId: this.config.id,
      itemCount: items.length,
      items,
      downloadedFiles,
      errors: this.errors.length > 0 ? this.errors : undefined,
      metadata: {
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs: Date.now() - startTime.getTime(),
        pagesProcessed,
      },
    };
  }

  protected delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ============ 더불어민주당 Crawler ============
class PartyMinjooCrawler extends BaseCrawler {
  constructor() {
    super({
      id: 'party_minjoo',
      name: '더불어민주당',
      baseUrl: 'https://theminjoo.kr',
    });
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      console.log('[Minjoo] Starting crawl...');

      // 선거자료실 크롤링
      const electionItems = await this.crawlBoard(16, '선거자료실', options);
      items.push(...electionItems);
      pagesProcessed++;

      // 정책자료실 크롤링 (brd=19)
      if (options.filters?.includePolicy) {
        const policyItems = await this.crawlBoard(19, '정책자료실', options);
        items.push(...policyItems);
        pagesProcessed++;
      }

      // PDF 다운로드
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

      console.log(`[Minjoo] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      console.error(`[Minjoo] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

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
      console.log(`  [Minjoo] Crawling ${boardName} page ${page}`);

      try {
        const html = await this.fetchPage(url);
        const $ = this.parseHtml(html);

        // 실제 구조: <a href="./view.php?..."><span data-brl-use="PH/2">제목</span></a>
        $('a[href*="view.php"]').each((i, el) => {
          const $el = $(el);
          const link = $el.attr('href');

          // 네비게이션 링크 제외 (brd 파라미터가 현재 보드와 같아야 함)
          if (!link || !link.includes(`brd=${boardId}`)) return;

          const title = $el.find('span').text().trim() || $el.text().trim();

          if (!title || title.length < 5) return;

          const fullUrl = link.startsWith('http')
            ? link
            : link.startsWith('./')
              ? `${this.config.baseUrl}/main/sub/news/${link.substring(2)}`
              : `${this.config.baseUrl}${link}`;

          const dateText = '';

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

        await this.delay(CRAWL_SETTINGS.REQUEST_DELAY_MS);
      } catch (error: any) {
        this.addError(url, error.message);
      }
    }

    // 상세 페이지에서 PDF 링크 추출 (처음 5개만)
    const itemsToFetch = items.slice(0, 5);
    for (const item of itemsToFetch) {
      if (item.url && item.url !== this.config.baseUrl) {
        try {
          const detailHtml = await this.fetchPage(item.url);
          const $detail = this.parseHtml(detailHtml);

          const pdfLink = $detail('a[href$=".pdf"]').first().attr('href');
          if (pdfLink) {
            item.fileUrl = pdfLink.startsWith('http')
              ? pdfLink
              : `${this.config.baseUrl}${pdfLink}`;
          }

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
    const match = dateText.match(/(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})/);
    if (match && match[1] && match[2] && match[3]) {
      const year = match[1];
      const month = match[2];
      const day = match[3];
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    return undefined;
  }
}

// ============ 국민의힘 Crawler ============
class PartyPPPCrawler extends BaseCrawler {
  constructor() {
    super({
      id: 'party_ppp',
      name: '국민의힘',
      baseUrl: 'https://www.peoplepowerparty.kr',
    });
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      console.log('[PPP] Starting crawl...');

      // 정책자료실 크롤링 (새 URL 구조)
      const policyItems = await this.crawlDataPolicy(options);
      items.push(...policyItems);
      pagesProcessed++;

      // 공약자료실 크롤링
      const pledgeItems = await this.crawlDataPledge(options);
      items.push(...pledgeItems);
      pagesProcessed++;

      // PDF 다운로드
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

      console.log(`[PPP] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      console.error(`[PPP] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  private async crawlDataPolicy(options: CrawlOptions): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/news/data_policy`;

    console.log(`  [PPP] Crawling policy data: ${url}`);

    try {
      const browser = await this.initBrowser();
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

      // 동적 콘텐츠 대기
      await this.delay(3000);

      // 페이지에서 게시글 목록 추출
      const posts = await page.evaluate(() => {
        const results: { title: string; link: string; date: string }[] = [];

        // 게시글 목록 찾기 (다양한 셀렉터 시도)
        const selectors = [
          '.board-list li a',
          '.bbs-list li a',
          '.news-list li a',
          '.list-wrap li a',
          'table tbody tr',
          '.data-list .item',
          '.article-list .item',
        ];

        for (const selector of selectors) {
          const elements = document.querySelectorAll(selector);
          if (elements.length > 0) {
            elements.forEach((el) => {
              let title = '';
              let link = '';
              let date = '';

              if (el.tagName === 'TR') {
                const titleEl = el.querySelector('td a, .title a');
                title = titleEl?.textContent?.trim() || '';
                link = titleEl?.getAttribute('href') || '';
                const dateEl = el.querySelector('.date, td:last-child');
                date = dateEl?.textContent?.trim() || '';
              } else if (el.tagName === 'A') {
                title = el.textContent?.trim() || '';
                link = el.getAttribute('href') || '';
              } else {
                const titleEl = el.querySelector('a, .title');
                title = titleEl?.textContent?.trim() || '';
                link = titleEl?.getAttribute('href') || '';
              }

              if (title && title.length > 5 && link) {
                results.push({ title, link, date });
              }
            });
            break;
          }
        }

        // 대체: 모든 링크에서 /news/data_policy/view 패턴 찾기
        if (results.length === 0) {
          const allLinks = document.querySelectorAll('a[href*="/news/data_policy/"]');
          allLinks.forEach((el) => {
            const title = el.textContent?.trim() || '';
            const link = el.getAttribute('href') || '';
            if (title && title.length > 5) {
              results.push({ title, link, date: '' });
            }
          });
        }

        return results;
      });

      await page.close();

      console.log(`    Found ${posts.length} policy posts`);

      for (const post of posts) {
        const fullUrl = post.link.startsWith('http')
          ? post.link
          : `${this.config.baseUrl}${post.link}`;

        items.push({
          id: `ppp-policy-${Date.now()}-${items.length}`,
          title: post.title,
          url: fullUrl,
          date: post.date,
          category: '정책자료실',
          metadata: {
            partyName: '국민의힘',
            sourceSite: 'party_ppp',
          },
        });
      }
    } catch (error: any) {
      this.addError(url, error.message);
    }

    return items;
  }

  private async crawlDataPledge(options: CrawlOptions): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/news/data_pledge`;

    console.log(`  [PPP] Crawling pledge data: ${url}`);

    try {
      const browser = await this.initBrowser();
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

      await this.delay(3000);

      // 공약 자료 추출
      const posts = await page.evaluate(() => {
        const results: { title: string; link: string; date: string }[] = [];

        // 링크에서 /news/data_pledge/ 패턴 찾기
        const allLinks = document.querySelectorAll('a[href*="/news/data_pledge/"], a[href*="data_pledge"]');
        allLinks.forEach((el) => {
          const title = el.textContent?.trim() || '';
          const link = el.getAttribute('href') || '';
          if (title && title.length > 5 && !link.includes('page=')) {
            results.push({ title, link, date: '' });
          }
        });

        // 게시판 형태로도 시도
        const boardItems = document.querySelectorAll('.board-list li, .bbs-list li, table tbody tr');
        boardItems.forEach((item) => {
          const linkEl = item.querySelector('a');
          if (linkEl) {
            const title = linkEl.textContent?.trim() || '';
            const link = linkEl.getAttribute('href') || '';
            if (title && title.length > 5 && !results.some((r) => r.link === link)) {
              results.push({ title, link, date: '' });
            }
          }
        });

        return results;
      });

      await page.close();

      console.log(`    Found ${posts.length} pledge posts`);

      for (const post of posts) {
        const fullUrl = post.link.startsWith('http')
          ? post.link
          : `${this.config.baseUrl}${post.link}`;

        items.push({
          id: `ppp-pledge-${Date.now()}-${items.length}`,
          title: post.title,
          url: fullUrl,
          date: post.date,
          category: '공약자료실',
          metadata: {
            partyName: '국민의힘',
            sourceSite: 'party_ppp',
          },
        });
      }
    } catch (error: any) {
      this.addError(url, error.message);
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
}

// ============ NEC Policy Crawler ============
class NecPolicyCrawler extends BaseCrawler {
  // NEC PDF 베이스 URL
  private readonly PDF_BASE_URL = 'https://policy.nec.go.kr/plc/cmm/downloadFile.do?dataPath=';

  constructor() {
    super({
      id: 'nec_policy',
      name: '정책·공약마당',
      baseUrl: 'https://policy.nec.go.kr',
    });
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      console.log('[NEC Policy] Starting crawl...');

      // 정당 정책 목록 크롤링 (PARTY5 = 정당정책)
      const partyPolicies = await this.crawlPartyPolicies('PARTY5', options);
      items.push(...partyPolicies);
      pagesProcessed++;

      // PDF 다운로드
      if (options.downloadFiles && options.outputDir) {
        for (const item of items) {
          if (item.fileUrl) {
            try {
              const filePath = await this.downloadPdf(
                item.fileUrl,
                options.outputDir,
                item
              );
              if (filePath) {
                downloadedFiles.push(filePath);
              }
            } catch (err: any) {
              this.addError(item.fileUrl, `PDF download failed: ${err.message}`);
            }
          }
        }
      }

      console.log(`[NEC Policy] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      console.error(`[NEC Policy] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  private async crawlPartyPolicies(
    menuId: string,
    options: CrawlOptions
  ): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/plc/policy/initUPAPolicy.do?menuId=${menuId}`;

    console.log(`  [NEC Policy] Crawling party policies: ${menuId}`);

    try {
      // Puppeteer로 동적 콘텐츠 로드
      const browser = await this.initBrowser();
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

      // 추가 대기 (동적 콘텐츠 로드)
      await this.delay(3000);

      // 페이지에서 직접 정당 정보와 PDF 링크 추출
      const partyData = await page.evaluate(() => {
        const results: { partyName: string; pdfPath: string; fileName: string }[] = [];

        // onclick 속성에서 _FN_VIEW_PDF_DOWN 호출 찾기
        // 형식: _FN_VIEW_PDF_DOWN('파일명.pdf', '경로/파일.pdf')
        const pdfDownloadElements = document.querySelectorAll('[onclick*="_FN_VIEW_PDF_DOWN"]');

        pdfDownloadElements.forEach((el) => {
          const onclick = el.getAttribute('onclick') || '';
          // _FN_VIEW_PDF_DOWN('20250603_더불어민주당_정당정책.pdf', '20250603/PDF/PARTY_PLC_PUB/007_100_20250510_1.pdf')
          const match = onclick.match(/_FN_VIEW_PDF_DOWN\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)/);

          if (match) {
            const fileName = match[1];
            const pdfPath = match[2];

            // 파일명에서 정당명 추출 (예: 20250603_더불어민주당_정당정책.pdf)
            const partyMatch = fileName.match(/_([^_]+)_정당정책/);
            const partyName = partyMatch ? partyMatch[1] : '알수없음';

            results.push({ partyName, pdfPath, fileName });
          }
        });

        // 정당별 박스에서도 정보 추출 (.commit_l_box)
        const partyBoxes = document.querySelectorAll('.commit_l_box');
        partyBoxes.forEach((box) => {
          const nameEl = box.querySelector('em');
          const partyName = nameEl?.textContent?.trim() || '';

          if (partyName) {
            // 이미 추출된 정당인지 확인
            const existing = results.find((r) => r.partyName === partyName);
            if (!existing) {
              // PDF 버튼 찾기
              const pdfBtn = box.querySelector('[onclick*="_FN_VIEW_PDF_DOWN"]');
              if (pdfBtn) {
                const onclick = pdfBtn.getAttribute('onclick') || '';
                const match = onclick.match(/_FN_VIEW_PDF_DOWN\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)/);
                if (match) {
                  results.push({
                    partyName,
                    pdfPath: match[2],
                    fileName: match[1],
                  });
                }
              }
            }
          }
        });

        return results;
      });

      await page.close();

      console.log(`    Found ${partyData.length} party policy PDFs`);

      // CrawledItem으로 변환
      for (const data of partyData) {
        const pdfUrl = `${this.PDF_BASE_URL}${encodeURIComponent(data.pdfPath)}&orginlFileNm=${encodeURIComponent(data.fileName)}`;

        items.push({
          id: `nec-policy-${data.partyName}-${Date.now()}`,
          title: `${data.partyName} 정당정책`,
          url,
          fileUrl: pdfUrl,
          category: 'policy_pdf',
          metadata: {
            partyName: data.partyName,
            menuId,
            sourceSite: 'nec_policy',
            originalFileName: data.fileName,
            pdfPath: data.pdfPath,
          },
        });

        console.log(`    - ${data.partyName}: ${data.fileName}`);
      }
    } catch (error: any) {
      this.addError(url, error.message);
    }

    return items;
  }

  private async downloadPdf(
    url: string,
    outputDir: string,
    item: CrawledItem
  ): Promise<string | null> {
    try {
      const fileName = item.metadata?.originalFileName || `${item.metadata?.partyName || 'unknown'}_정책.pdf`;
      const safeFileName = fileName.replace(/[^a-zA-Z0-9가-힣_.]/g, '_');

      const filePath = await this.downloadFile(url, outputDir, safeFileName);
      console.log(`    Downloaded: ${safeFileName}`);

      return filePath;
    } catch (error: any) {
      console.error(`    Download failed: ${error.message}`);
      return null;
    }
  }

  private normalizePartyName(name: string): string {
    const nameMap: Record<string, string> = {
      민주당: '더불어민주당',
      국힘: '국민의힘',
      미래통합당: '국민의힘',
      자유한국당: '국민의힘',
    };

    const trimmedName = name.trim();
    return nameMap[trimmedName] || trimmedName;
  }
}

// ============ Crawler Factory ============
function createCrawler(type: string): BaseCrawler {
  switch (type) {
    case 'party_minjoo':
      return new PartyMinjooCrawler();
    case 'party_ppp':
      return new PartyPPPCrawler();
    case 'nec_policy':
      return new NecPolicyCrawler();
    default:
      throw new Error(`Unknown crawler type: ${type}`);
  }
}

// ============ Main ============
async function main(): Promise<void> {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('   naPO 대규모 크롤링 시작 (Standalone)');
  console.log('   시작 시간:', new Date().toLocaleString('ko-KR'));
  console.log('═══════════════════════════════════════════════════════════');

  // 인자 파싱
  const args = process.argv.slice(2);
  const targetCrawler = args.find(a => a.startsWith('--crawler='))?.split('=')[1];
  const downloadFiles = args.includes('--download');
  const pagesArg = args.find(a => a.startsWith('--pages='))?.split('=')[1];
  const endPage = pagesArg ? parseInt(pagesArg, 10) : 3;

  // 디렉토리 생성
  const logDir = path.join(BASE_OUTPUT_DIR, 'logs');
  await fs.mkdir(logDir, { recursive: true });

  // 크롤링 옵션
  const crawlOptions: CrawlOptions = {
    startPage: 1,
    endPage,
    downloadFiles,
    outputDir: BASE_OUTPUT_DIR,
    filters: {
      includePolicy: true,
      includeCandidates: false,
    },
  };

  console.log('\n📋 크롤링 설정:');
  console.log(`   - 페이지 범위: 1~${endPage}`);
  console.log(`   - PDF 다운로드: ${downloadFiles ? '활성화' : '비활성화'}`);
  console.log(`   - 대상: ${targetCrawler || '모든 크롤러'}`);

  // 크롤링 대상
  const targets = targetCrawler
    ? [targetCrawler]
    : ['nec_policy', 'party_minjoo', 'party_ppp'];

  const allStats: any[] = [];

  for (const target of targets) {
    console.log(`\n🚀 [${target}] 크롤링 시작...`);
    const startTime = Date.now();

    try {
      const outputDir = path.join(BASE_OUTPUT_DIR, target, 'pdf');
      await fs.mkdir(outputDir, { recursive: true });

      const crawler = createCrawler(target);
      const result = await crawler.crawl({
        ...crawlOptions,
        outputDir,
      });

      // 결과 저장
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const jsonPath = path.join(BASE_OUTPUT_DIR, target, 'json', `crawl_${timestamp}.json`);
      await fs.mkdir(path.dirname(jsonPath), { recursive: true });
      await fs.writeFile(jsonPath, JSON.stringify(result, null, 2), 'utf-8');

      const stats = {
        crawler: target,
        status: result.success ? 'success' : 'partial',
        itemCount: result.itemCount,
        downloadedFiles: result.downloadedFiles?.length || 0,
        errors: result.errors?.length || 0,
        durationMs: Date.now() - startTime,
      };

      console.log(`  ✅ 완료: ${stats.itemCount}개 항목, ${stats.downloadedFiles}개 파일`);
      if (stats.errors > 0) {
        console.log(`  ⚠️  에러: ${stats.errors}개`);
      }
      console.log(`  📁 저장: ${jsonPath}`);

      allStats.push(stats);
    } catch (error: any) {
      console.error(`  ❌ 실패: ${error.message}`);
      allStats.push({
        crawler: target,
        status: 'failed',
        itemCount: 0,
        downloadedFiles: 0,
        errors: 1,
        durationMs: Date.now() - startTime,
      });
    }

    // 크롤러 간 딜레이
    if (targets.indexOf(target) < targets.length - 1) {
      console.log('\n⏳ 다음 크롤러 대기 (5초)...');
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }

  // 최종 보고서
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('   크롤링 완료 보고서');
  console.log('═══════════════════════════════════════════════════════════');

  let totalItems = 0;
  let totalFiles = 0;
  let totalErrors = 0;
  let totalDuration = 0;

  for (const stats of allStats) {
    const statusIcon =
      stats.status === 'success' ? '✅' :
      stats.status === 'partial' ? '⚠️' : '❌';

    console.log(`\n${statusIcon} ${stats.crawler}:`);
    console.log(`   - 항목: ${stats.itemCount}개`);
    console.log(`   - 파일: ${stats.downloadedFiles}개`);
    console.log(`   - 에러: ${stats.errors}개`);
    console.log(`   - 소요: ${(stats.durationMs / 1000).toFixed(1)}초`);

    totalItems += stats.itemCount;
    totalFiles += stats.downloadedFiles;
    totalErrors += stats.errors;
    totalDuration += stats.durationMs;
  }

  console.log('\n───────────────────────────────────────────────────────────');
  console.log(`📊 총계:`);
  console.log(`   - 총 항목: ${totalItems}개`);
  console.log(`   - 총 파일: ${totalFiles}개`);
  console.log(`   - 총 에러: ${totalErrors}개`);
  console.log(`   - 총 소요: ${(totalDuration / 1000 / 60).toFixed(1)}분`);
  console.log(`   - 종료 시간: ${new Date().toLocaleString('ko-KR')}`);
  console.log('═══════════════════════════════════════════════════════════\n');

  // 로그 저장
  const logPath = path.join(logDir, `crawl_${new Date().toISOString().split('T')[0]}.json`);
  const logContent = {
    startTime: new Date(Date.now() - totalDuration).toISOString(),
    endTime: new Date().toISOString(),
    stats: allStats,
    totals: { totalItems, totalFiles, totalErrors, totalDuration },
  };
  await fs.writeFile(logPath, JSON.stringify(logContent, null, 2), 'utf-8');
  console.log(`📝 로그 저장: ${logPath}`);
}

main().catch(console.error);
