import { PdfParser } from './baseParser';
import { PyMuPdfParser } from './pymupdfParser';
import { ClovaOcrParser } from './clovaParser';
import { GoogleVisionParser } from './googleVisionParser';
import { DolphinParser } from './dolphinParser';
import { ParserType } from '@/types/parser.types';
import { logger } from '@/config/logger';

export class ParserFactory {
  private static parsers: Map<ParserType, () => PdfParser> = new Map<ParserType, () => PdfParser>([
    ['pymupdf', () => new PyMuPdfParser()],
    ['clova_ocr', () => new ClovaOcrParser()],
    ['google_vision', () => new GoogleVisionParser()],
    ['dolphin', () => new DolphinParser()],
  ]);

  static create(type: ParserType): PdfParser {
    const factory = this.parsers.get(type);
    if (!factory) {
      throw new Error(`Unknown parser type: ${type}`);
    }
    return factory();
  }

  static async getAvailableParsers(): Promise<ParserType[]> {
    const available: ParserType[] = [];

    for (const [type, factory] of this.parsers) {
      const parser = factory();
      if (await parser.isAvailable()) {
        available.push(type);
      }
    }

    return available;
  }

  // 자동 선택: 최적 파서 반환
  static async selectBestParser(file: Buffer): Promise<PdfParser> {
    // 1. 메타데이터 기반으로 먼저 확인 (파싱 없이 빠르게 판단)
    // PDF 헤더와 기본 구조 확인
    const hasPdfHeader = file.subarray(0, 5).toString('ascii') === '%PDF-';
    if (!hasPdfHeader) {
      throw new Error('Invalid PDF file');
    }

    // 2. 텍스트 추출 가능한지 확인 (PyMuPDF) - 첫 페이지만 테스트
    const pymupdf = new PyMuPdfParser();
    try {
      // 첫 페이지만 파싱하여 텍스트가 충분한지 확인
      const testResult = await pymupdf.parse(file, { pageRange: { start: 1, end: 1 } });

      // 텍스트가 충분하면 PyMuPDF 사용 (OCR 불필요)
      if (testResult.content.text.trim().length > 100) {
        logger.debug('[ParserFactory] Selected PyMuPDF (text extractable)');
        return pymupdf;
      }

      // 텍스트가 부족하면 OCR 필요
      logger.debug('[ParserFactory] PDF has insufficient text, OCR needed');
    } catch (error: any) {
      logger.warn('[ParserFactory] PyMuPDF test failed:', { error: error.message });
    }

    // 3. OCR 필요 → 사용 가능한 OCR 파서 찾기
    const clova = new ClovaOcrParser();
    if (await clova.isAvailable()) {
      logger.debug('[ParserFactory] Selected Clova OCR');
      return clova;
    }

    // 4. Google Vision도 확인
    const googleVision = new GoogleVisionParser();
    if (await googleVision.isAvailable()) {
      logger.debug('[ParserFactory] Selected Google Vision OCR');
      return googleVision;
    }

    // 5. Fallback to PyMuPDF (텍스트가 적더라도 최선의 선택)
    logger.debug('[ParserFactory] Fallback to PyMuPDF (no OCR available)');
    return pymupdf;
  }
}
