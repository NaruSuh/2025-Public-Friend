/**
 * NEC 정책·공약마당 크롤러
 * https://policy.nec.go.kr
 *
 * 크롤링 대상:
 * - 정당 정책 (PARTY5, PARTY6)
 * - 후보자 공약 (CNDDT20)
 * - 공약이슈트리 (SURVEY1)
 * - PDF 공약집 다운로드
 */

import { BaseCrawler } from './baseCrawler';
import {
  CrawlerSiteConfig,
  CrawlOptions,
  CrawlResult,
  CrawledItem,
} from '@/types/crawler.types';
import { logger } from '@/config/logger';
import type { CheerioAPI } from 'cheerio';

const NEC_POLICY_CONFIG: CrawlerSiteConfig = {
  id: 'nec_policy',
  name: '정책·공약마당',
  baseUrl: 'https://policy.nec.go.kr',
  selectors: {
    listContainer: '.policy-list, .plcList',
    listItem: '.policy-item, .plcItem, tr',
    title: '.policy-title, .plcTit, .title',
    content: '.policy-content, .plcCont',
    link: 'a',
    pdfLink: 'a[href*="downloadFile"], a[href$=".pdf"]',
  },
  authentication: {
    type: 'none',
  },
};

// 정당 메뉴 ID 매핑
const PARTY_MENU_IDS = {
  PARTY5: '정당정책 (1페이지)',
  PARTY6: '정당정책 (2페이지)',
};

// 주요 정당 정보 (향후 정당 필터링 및 검증에 사용 예정)
const MAJOR_PARTIES = [
  { name: '더불어민주당', keywords: ['더불어민주당', '민주당'] },
  { name: '국민의힘', keywords: ['국민의힘', '국힘'] },
  { name: '조국혁신당', keywords: ['조국혁신당'] },
  { name: '개혁신당', keywords: ['개혁신당'] },
  { name: '진보당', keywords: ['진보당'] },
  { name: '기본소득당', keywords: ['기본소득당'] },
  { name: '사회민주당', keywords: ['사회민주당'] },
] as const;

export class NecPolicyCrawler extends BaseCrawler {
  constructor() {
    super(NEC_POLICY_CONFIG);
  }

  async crawl(options: CrawlOptions): Promise<CrawlResult> {
    const startTime = new Date();
    const items: CrawledItem[] = [];
    const downloadedFiles: string[] = [];
    let pagesProcessed = 0;

    try {
      // 1. 정당 정책 목록 크롤링
      logger.info('[NEC Policy] Starting crawl...');

      for (const menuId of Object.keys(PARTY_MENU_IDS)) {
        const partyPolicies = await this.crawlPartyPolicies(menuId, options);
        items.push(...partyPolicies);
        pagesProcessed++;
      }

      // 2. 후보자 공약 크롤링 (선거 진행 중일 때만)
      if (options.filters?.includeCandidates) {
        const candidatePledges = await this.crawlCandidatePledges(options);
        items.push(...candidatePledges);
        pagesProcessed++;
      }

      // 3. PDF 다운로드 (옵션)
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

      logger.info(`[NEC Policy] Crawl complete. Items: ${items.length}`);
    } catch (error: any) {
      logger.error(`[NEC Policy] Crawl error: ${error.message}`);
      this.addError(this.config.baseUrl, error.message);
    } finally {
      await this.closeBrowser();
    }

    return this.buildResult(items, startTime, pagesProcessed, downloadedFiles);
  }

  /**
   * 정당 정책 목록 크롤링
   */
  private async crawlPartyPolicies(
    menuId: string,
    options: CrawlOptions
  ): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/plc/policy/initUPAPolicy.do?menuId=${menuId}`;

    logger.debug(`[NEC Policy] Crawling party policies: ${url}`);

    try {
      const html = await this.fetchWithPuppeteer(url);
      const $ = this.parseHtml(html);

      // 정당별 블록 파싱
      $('.party-block, .partyBox, [class*="party"]').each((_, partyBlock) => {
        const $party = $(partyBlock);
        const partyName = this.extractPartyName($party);

        if (!partyName) return;

        // 정당 필터링 (옵션)
        if (options.filters?.partyName) {
          if (!partyName.includes(options.filters.partyName)) return;
        }

        // 정책 항목들 파싱
        $party.find('.policy-item, .plcItem, li').each((i, policyEl) => {
          const $policy = $(policyEl);

          const title =
            $policy.find('.title, .plcTit').text().trim() ||
            $policy.text().trim().substring(0, 100);

          const pdfLink = $policy.find('a[href*="downloadFile"]').attr('href');
          const fullPdfUrl = pdfLink
            ? `${this.config.baseUrl}${pdfLink}`
            : undefined;

          if (title) {
            items.push({
              id: `nec-policy-${partyName}-${i}-${Date.now()}`,
              title,
              url,
              fileUrl: fullPdfUrl,
              category: 'policy',
              metadata: {
                partyName,
                menuId,
                electionType: this.detectElectionType($),
                sourceSite: 'nec_policy',
              },
            });
          }
        });
      });

      // 직접 PDF 링크 추출 (테이블 형식)
      $('table tr').each((i, row) => {
        const $row = $(row);
        const partyName = $row.find('td').eq(0).text().trim();
        const pdfLink = $row.find('a[href*="downloadFile"], a[href$=".pdf"]').attr('href');

        if (partyName && pdfLink) {
          const normalizedParty = this.normalizePartyName(partyName);
          items.push({
            id: `nec-policy-pdf-${normalizedParty}-${i}-${Date.now()}`,
            title: `${normalizedParty} 정책공약집`,
            url,
            fileUrl: pdfLink.startsWith('http') ? pdfLink : `${this.config.baseUrl}${pdfLink}`,
            category: 'policy_pdf',
            metadata: {
              partyName: normalizedParty,
              sourceSite: 'nec_policy',
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
   * 후보자 공약 크롤링
   */
  private async crawlCandidatePledges(options: CrawlOptions): Promise<CrawledItem[]> {
    const items: CrawledItem[] = [];
    const url = `${this.config.baseUrl}/plc/commiment/initUCACommiment.do?menuId=CNDDT20`;

    logger.debug(`[NEC Policy] Crawling candidate pledges: ${url}`);

    try {
      const html = await this.fetchWithPuppeteer(url);
      const $ = this.parseHtml(html);

      // 후보자별 공약 파싱
      $('.candidate-item, .cndtBox').each((i, candidateEl) => {
        const $candidate = $(candidateEl);

        const candidateName = $candidate.find('.name, .cndtName').text().trim();
        const partyName = $candidate.find('.party, .partyName').text().trim();
        const constituency = $candidate.find('.area, .elecArea').text().trim();
        const pdfLink = $candidate.find('a[href*="downloadFile"]').attr('href');

        if (candidateName) {
          items.push({
            id: `nec-candidate-${candidateName}-${i}-${Date.now()}`,
            title: `${candidateName} 공약`,
            url,
            fileUrl: pdfLink ? `${this.config.baseUrl}${pdfLink}` : undefined,
            category: 'candidate_pledge',
            metadata: {
              candidateName,
              partyName: this.normalizePartyName(partyName),
              constituency,
              sourceSite: 'nec_policy',
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
   * PDF 다운로드
   */
  private async downloadPdf(
    url: string,
    outputDir: string,
    item: CrawledItem
  ): Promise<string | null> {
    try {
      const partyName = item.metadata?.partyName || 'unknown';
      const safePartyName = partyName.replace(/[^a-zA-Z0-9가-힣]/g, '_');
      const timestamp = new Date().toISOString().split('T')[0];
      const fileName = `nec_${safePartyName}_${timestamp}.pdf`;

      const filePath = await this.downloadFile(url, outputDir, fileName);
      logger.info(`[NEC Policy] Downloaded: ${fileName}`);

      return filePath;
    } catch (error: any) {
      logger.error(`[NEC Policy] Download failed: ${error.message}`);
      return null;
    }
  }

  /**
   * 정당명 추출
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private extractPartyName($element: any): string | null {
    // 여러 셀렉터 시도
    const selectors = ['.party-name', '.partyName', '.partyTit', 'h3', 'h4'];

    for (const selector of selectors) {
      const name = $element.find(selector).first().text().trim();
      if (name) {
        return this.normalizePartyName(name);
      }
    }

    return null;
  }

  /**
   * 정당명 정규화
   */
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

  /**
   * 선거 유형 감지
   */
  private detectElectionType($: CheerioAPI): string {
    const pageText = $('body').text();

    if (pageText.includes('대통령')) return 'presidential';
    if (pageText.includes('국회의원')) return 'legislative';
    if (pageText.includes('지방')) return 'local';

    return 'unknown';
  }

  /**
   * 크롤러 가용성 확인
   */
  async isAvailable(): Promise<boolean> {
    try {
      const response = await this.fetchPage(this.config.baseUrl);
      return response.includes('정책') || response.includes('공약');
    } catch {
      return false;
    }
  }
}
