import axios from 'axios';
import FormData from 'form-data';
import { BaseParser } from './baseParser';
import { ParseOptions, ParseResult, ParsedContent } from '@/types/parser.types';
import { env } from '@/config/env';

export class ClovaOcrParser extends BaseParser {
  parserId = 'clova_ocr' as const;
  parserName = 'Naver Clova OCR';

  async isAvailable(): Promise<boolean> {
    return !!(env.CLOVA_OCR_API_URL && env.CLOVA_OCR_SECRET_KEY);
  }

  async parse(file: Buffer, options?: ParseOptions): Promise<ParseResult> {
    const startTime = Date.now();
    const errors: string[] = [];

    if (!(await this.isAvailable())) {
      errors.push('Clova OCR credentials not configured');
      return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
    }

    try {
      const formData = new FormData();
      formData.append('file', file, {
        filename: 'document.pdf',
        contentType: 'application/pdf',
      });
      formData.append(
        'message',
        JSON.stringify({
          version: 'V2',
          requestId: `napo-${Date.now()}`,
          timestamp: Date.now(),
          lang: options?.language || 'ko',
          images: [{ format: 'pdf', name: 'document' }],
        })
      );

      const response = await axios.post(env.CLOVA_OCR_API_URL!, formData, {
        headers: {
          'X-OCR-SECRET': env.CLOVA_OCR_SECRET_KEY!,
          ...formData.getHeaders(),
        },
        timeout: 120000,
      });

      // Clova OCR 응답 파싱
      const result = response.data;
      const extractedText = this.extractTextFromClovaResponse(result);

      const content: ParsedContent = {
        text: extractedText,
        structuredData: result,
      };

      return this.buildResult(
        'document.pdf',
        content,
        result.images?.length || 1,
        Date.now() - startTime,
        this.calculateConfidence(result)
      );
    } catch (error: any) {
      errors.push(error.message);
      return this.buildResult('document.pdf', { text: '' }, 0, Date.now() - startTime, 0, errors);
    }
  }

  private extractTextFromClovaResponse(response: any): string {
    const texts: string[] = [];

    if (response.images) {
      for (const image of response.images) {
        if (image.fields) {
          for (const field of image.fields) {
            if (field.inferText) {
              texts.push(field.inferText);
            }
          }
        }
      }
    }

    return texts.join('\n');
  }

  private calculateConfidence(response: any): number {
    let totalConfidence = 0;
    let count = 0;

    if (response.images) {
      for (const image of response.images) {
        if (image.fields) {
          for (const field of image.fields) {
            if (typeof field.inferConfidence === 'number') {
              totalConfidence += field.inferConfidence;
              count++;
            }
          }
        }
      }
    }

    return count > 0 ? totalConfidence / count : 0;
  }
}
