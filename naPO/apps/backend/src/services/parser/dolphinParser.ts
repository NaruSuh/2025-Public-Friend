import axios from 'axios';
import FormData from 'form-data';
import { BaseParser } from './baseParser';
import { ParserType, ParseOptions, ParseResult, ParsedContent, PageContent } from '@/types/parser.types';
import { env } from '@/config/env';
import { logger } from '@/config/logger';

export class DolphinParser extends BaseParser {
  parserId: ParserType = 'dolphin';
  parserName = 'Dolphin Layout Analysis';

  private serviceUrl = env.DOLPHIN_SERVICE_URL || 'http://localhost:8765';

  async isAvailable(): Promise<boolean> {
    try {
      // Check if Dolphin service is running
      const response = await axios.get(`${this.serviceUrl}/health`, {
        timeout: 5000,
      });
      return response.data?.model_loaded === true;
    } catch (error: any) {
      logger.warn('Dolphin service not available:', { error: error.message });
      return false;
    }
  }

  async parse(file: Buffer, options?: ParseOptions): Promise<ParseResult> {
    const startTime = Date.now();
    const errors: string[] = [];

    if (!(await this.isAvailable())) {
      errors.push('Dolphin service not available. Make sure dolphin_service.py is running on port 8765.');
      return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
    }

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append('file', file, {
        filename: 'document.pdf',
        contentType: 'application/pdf',
      });
      formData.append('language', options?.language || 'en');
      formData.append('extract_layout', 'true');

      // Send request to Dolphin service
      const response = await axios.post(`${this.serviceUrl}/parse`, formData, {
        headers: {
          ...formData.getHeaders(),
        },
        timeout: 180000, // 3 minutes timeout for large documents
      });

      const result = response.data;

      if (!result.success) {
        errors.push(result.error || 'Parsing failed');
        return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
      }

      // Transform pages to PageContent format
      const pages: PageContent[] = result.pages.map((page: any) => ({
        pageNumber: page.pageNumber,
        text: page.text,
      }));

      const content: ParsedContent = {
        text: result.text,
        pages,
        metadata: result.metadata,
      };

      return this.buildResult(
        'document.pdf',
        content,
        result.metadata?.pageCount || pages.length,
        Date.now() - startTime,
        0.95 // Dolphin has high confidence
      );
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED') {
        errors.push('Cannot connect to Dolphin service. Is dolphin_service.py running?');
      } else if (error.code === 'ETIMEDOUT') {
        errors.push('Dolphin service timeout. Document may be too large.');
      } else {
        errors.push(error.message);
      }
      return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
    }
  }
}
