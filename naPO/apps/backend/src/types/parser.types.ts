export type ParserType = 'clova_ocr' | 'google_vision' | 'pymupdf' | 'dolphin';

export interface ParseOptions {
  language?: string; // 'ko', 'en', 'mixed'
  extractTables?: boolean;
  extractImages?: boolean;
  pageRange?: {
    start: number;
    end: number;
  };
  outputFormat?: 'text' | 'json' | 'markdown';
}

export interface ParseResult {
  success: boolean;
  parserId: ParserType;
  fileName: string;
  pageCount: number;
  content: ParsedContent;
  metadata: {
    parseTimeMs: number;
    confidence?: number;
  };
  errors?: string[];
}

export interface ParsedContent {
  text: string;
  pages?: PageContent[];
  tables?: TableData[];
  images?: ImageData[];
  structuredData?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface PageContent {
  pageNumber: number;
  text: string;
  tables?: TableData[];
  images?: ImageData[];
}

export interface TableData {
  pageNumber: number;
  rows: string[][];
  headers?: string[];
}

export interface ImageData {
  pageNumber: number;
  imageIndex: number;
  base64?: string;
  extractedText?: string;
}
