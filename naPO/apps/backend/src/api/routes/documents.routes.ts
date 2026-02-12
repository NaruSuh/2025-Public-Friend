import { Router } from 'express';
import type { Router as IRouter } from 'express';
import { body, validationResult } from 'express-validator';
import { EmbeddingService } from '@/services/rag/embeddingService';
import { DocumentIngestor } from '@/services/rag/documentIngestor';
import { getRagDb } from '@/services/rag/ragDb';

const router: IRouter = Router();

router.post(
  '/ingest',
  body('rootPath').optional().isString(),
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ message: 'Invalid request', errors: errors.array() });
      }

      const rootPath = (req.body?.rootPath as string | undefined) || undefined;
      const embedder = new EmbeddingService(process.env.GEMINI_API_KEY);
      const ingestor = new DocumentIngestor(embedder);
      const stats = await ingestor.ingestAll(rootPath);
      return res.json({ status: 'ok', stats });
    } catch (error) {
      return next(error);
    }
  }
);

router.get('/stats', (req, res, next) => {
  try {
    const db = getRagDb();
    const docCount = db.prepare('SELECT COUNT(*) as count FROM documents').get() as { count: number };
    const chunkCount = db.prepare('SELECT COUNT(*) as count FROM chunks').get() as { count: number };
    return res.json({ documents: docCount.count, chunks: chunkCount.count });
  } catch (error) {
    return next(error);
  }
});

export default router;
