import { ParserType, ParseOptions, ParseResult, ParsedContent } from '@/types/parser.types';

/**
 * PDF 파서 인터페이스
 * 모든 PDF 파싱 구현체가 따라야 하는 계약을 정의합니다.
 */
export interface PdfParser {
  /** 파서 고유 식별자 */
  parserId: ParserType;
  /** 사용자에게 표시될 파서 이름 */
  parserName: string;

  /**
   * PDF 파일을 파싱합니다.
   * @param file - PDF 파일의 Buffer 데이터
   * @param options - 파싱 옵션 (페이지 범위, OCR 설정 등)
   * @returns 파싱 결과 (텍스트, 테이블, 메타데이터 포함)
   */
  parse(file: Buffer, options?: ParseOptions): Promise<ParseResult>;

  /**
   * 파서가 현재 사용 가능한지 확인합니다.
   * @returns 파서 사용 가능 여부
   */
  isAvailable(): Promise<boolean>;
}

/**
 * PDF 파서의 기본 추상 클래스
 * 공통 기능과 헬퍼 메서드를 제공합니다.
 *
 * @example
 * ```typescript
 * class MyParser extends BaseParser {
 *   parserId = 'myparser' as const;
 *   parserName = 'My Custom Parser';
 *
 *   async parse(file: Buffer, options?: ParseOptions): Promise<ParseResult> {
 *     // 구현...
 *     return this.buildResult(filename, content, pageCount, parseTime);
 *   }
 * }
 * ```
 */
export abstract class BaseParser implements PdfParser {
  abstract parserId: ParserType;
  abstract parserName: string;

  abstract parse(file: Buffer, options?: ParseOptions): Promise<ParseResult>;

  /**
   * 파서가 현재 사용 가능한지 확인합니다.
   * 기본 구현은 항상 true를 반환합니다.
   * 외부 API를 사용하는 파서는 이를 오버라이드해야 합니다.
   */
  async isAvailable(): Promise<boolean> {
    return true;
  }

  /**
   * 표준화된 ParseResult 객체를 생성합니다.
   * @param fileName - 파싱된 파일명
   * @param content - 파싱된 콘텐츠 (텍스트, 페이지 등)
   * @param pageCount - 총 페이지 수
   * @param parseTimeMs - 파싱에 소요된 시간 (밀리초)
   * @param confidence - 파싱 신뢰도 점수 (0-1, 선택사항)
   * @param errors - 파싱 중 발생한 에러 목록 (선택사항)
   * @returns 표준화된 ParseResult 객체
   */
  protected buildResult(
    fileName: string,
    content: ParsedContent,
    pageCount: number,
    parseTimeMs: number,
    confidence?: number,
    errors?: string[]
  ): ParseResult {
    return {
      success: !errors || errors.length === 0,
      parserId: this.parserId,
      fileName,
      pageCount,
      content,
      metadata: {
        parseTimeMs,
        confidence,
      },
      errors,
    };
  }
}
