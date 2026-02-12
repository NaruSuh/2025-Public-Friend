import { EmbeddingService } from '@/services/rag/embeddingService';
import { DocumentIngestor } from '@/services/rag/documentIngestor';
import { logger } from '@/config/logger';

async function main() {
  const rootPath = process.argv[2];
  const embedder = new EmbeddingService(process.env.GEMINI_API_KEY);
  const ingestor = new DocumentIngestor(embedder);
  const stats = await ingestor.ingestAll(rootPath);
  logger.info('RAG ingest completed', stats);
}

main().catch((error) => {
  logger.error('RAG ingest failed', { error: error.message });
  process.exit(1);
});
