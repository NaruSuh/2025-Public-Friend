import { Parser } from '@json2csv/plainjs';
import fs from 'fs/promises';
import path from 'path';

export interface ExportOptions {
  fileName?: string;
  outputDir?: string;
  columns?: string[];
  delimiter?: string;
  includeHeader?: boolean;
}

export class CsvExporter {
  async export(
    data: any[],
    options: ExportOptions = {}
  ): Promise<{
    content: string;
    filePath?: string;
  }> {
    const { columns, delimiter = ',', includeHeader = true, fileName, outputDir } = options;

    // 데이터가 비어있으면 빈 문자열 반환
    if (!data || data.length === 0) {
      return { content: '' };
    }

    // 컬럼 자동 감지 또는 사용자 지정
    const fields = columns || Object.keys(data[0]);

    // JSON to CSV 변환
    const parser = new Parser({
      fields,
      delimiter,
      header: includeHeader,
    });

    const csv = parser.parse(data);

    // 파일 저장 (옵션)
    let filePath: string | undefined;
    if (fileName && outputDir) {
      await fs.mkdir(outputDir, { recursive: true });
      filePath = path.join(outputDir, fileName);
      await fs.writeFile(filePath, csv, 'utf-8');
    }

    return { content: csv, filePath };
  }

  // 스트리밍 내보내기 (대용량 데이터용)
  async exportStream(dataGenerator: AsyncGenerator<any>, options: ExportOptions): Promise<string> {
    const { outputDir, fileName } = options;

    if (!outputDir || !fileName) {
      throw new Error('outputDir and fileName are required for streaming export');
    }

    await fs.mkdir(outputDir, { recursive: true });
    const filePath = path.join(outputDir, fileName);

    let isFirst = true;
    let fields: string[] = [];

    for await (const item of dataGenerator) {
      if (isFirst) {
        fields = options.columns || Object.keys(item);
        const header = fields.join(',') + '\n';
        await fs.writeFile(filePath, header, 'utf-8');
        isFirst = false;
      }

      const row = fields.map((f) => this.escapeValue(item[f])).join(',') + '\n';
      await fs.appendFile(filePath, row, 'utf-8');
    }

    return filePath;
  }

  private escapeValue(value: any): string {
    if (value === null || value === undefined) {
      return '';
    }
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }
}
