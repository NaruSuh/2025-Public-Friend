import puppeteer, { Browser, Page } from 'puppeteer';
import * as cheerio from 'cheerio';
import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import {
  CrawlerSiteConfig,
  CrawlOptions,
  CrawlResult,
  CrawledItem,
  CrawlError,
} from '@/types/crawler.types';

export abstract class BaseCrawler {
  protected config: CrawlerSiteConfig;
  protected browser: Browser | null = null;
  protected errors: CrawlError[] = [];

  constructor(config: CrawlerSiteConfig) {
    this.config = config;
  }

  abstract crawl(options: CrawlOptions): Promise<CrawlResult>;

  protected async initBrowser(): Promise<Browser> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
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
}
