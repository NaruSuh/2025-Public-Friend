interface ChunkOptions {
  chunkSize?: number;
  overlap?: number;
}

interface ChunkResult {
  text: string;
  startOffset: number;
  endOffset: number;
}

const DEFAULT_CHUNK_SIZE = 800;
const DEFAULT_OVERLAP = 120;

export function chunkText(input: string, options: ChunkOptions = {}): ChunkResult[] {
  const chunkSize = options.chunkSize ?? DEFAULT_CHUNK_SIZE;
  const overlap = options.overlap ?? DEFAULT_OVERLAP;
  const normalized = input.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  if (!normalized) return [];

  const paragraphs = normalized.split(/\n{2,}/);
  const chunks: ChunkResult[] = [];
  let buffer = '';
  let bufferStart = 0;
  let cursor = 0;

  for (const para of paragraphs) {
    const block = para.trim();
    if (!block) {
      cursor += para.length + 2;
      continue;
    }

    if (buffer.length + block.length + 2 <= chunkSize) {
      if (!buffer) {
        bufferStart = cursor;
      }
      buffer = buffer ? `${buffer}\n\n${block}` : block;
    } else {
      if (buffer) {
        const prevStart = bufferStart;
        const prevLength = buffer.length;
        chunks.push({
          text: buffer,
          startOffset: bufferStart,
          endOffset: bufferStart + buffer.length,
        });

        const overlapText = buffer.slice(-overlap);
        buffer = overlapText ? `${overlapText}\n\n${block}` : block;
        bufferStart = Math.max(0, prevStart + prevLength - overlapText.length);
      } else {
        chunks.push({
          text: block,
          startOffset: cursor,
          endOffset: cursor + block.length,
        });
        buffer = '';
      }
    }

    cursor += para.length + 2;
  }

  if (buffer) {
    chunks.push({
      text: buffer,
      startOffset: bufferStart,
      endOffset: bufferStart + buffer.length,
    });
  }

  return chunks;
}
