import { BaseParser } from './baseParser';
import { ParserType, ParseOptions, ParseResult } from '@/types/parser.types';

export class GoogleVisionParser extends BaseParser {
  parserId: ParserType = 'google_vision';
  parserName = 'Google Vision OCR';

  async isAvailable(): Promise<boolean> {
    // Not yet implemented
    return false;
  }

  async parse(file: Buffer, options?: ParseOptions): Promise<ParseResult> {
    throw new Error(
      'Google Vision parser not yet implemented. ' +
        'This feature requires Google Cloud credentials and additional configuration. ' +
        'Please use PyMuPDF or Clova OCR parser instead.'
    );
  }
}
