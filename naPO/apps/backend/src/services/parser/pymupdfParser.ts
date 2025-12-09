import { BaseParser } from './baseParser';
import { ParseOptions, ParseResult, ParsedContent, PageContent } from '@/types/parser.types';
import pdf from 'pdf-parse';

export class PyMuPdfParser extends BaseParser {
  parserId = 'pymupdf' as const;
  parserName = 'PyMuPDF (Local)';

  async parse(file: Buffer, options?: ParseOptions): Promise<ParseResult> {
    const startTime = Date.now();
    const errors: string[] = [];

    try {
      const data = await pdf(file, {
        max: options?.pageRange?.end || 0,
      });

      const pages: PageContent[] = [];
      const textPerPage = data.text.split('\n\n');

      textPerPage.forEach((text: string, i: number) => {
        if (options?.pageRange) {
          const { start, end } = options.pageRange;
          if (i + 1 < start || i + 1 > end) return;
        }

        pages.push({
          pageNumber: i + 1,
          text: text.trim(),
        });
      });

      const content: ParsedContent = {
        text: data.text,
        pages,
      };

      return this.buildResult('document.pdf', content, data.numpages, Date.now() - startTime);
    } catch (error: any) {
      errors.push(error.message);
      return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
    }
  }
}
