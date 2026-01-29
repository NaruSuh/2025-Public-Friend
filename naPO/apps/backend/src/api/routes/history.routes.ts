import { Router, Request, Response } from 'express';
import { prisma } from '@/lib/prisma';

const router = Router();

// Helper function to extract error message
function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error';
}

// Get query history
router.get('/', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 50;
    const offset = parseInt(req.query.offset as string) || 0;

    const [history, total] = await Promise.all([
      prisma.queryHistory.findMany({
        orderBy: { createdAt: 'desc' },
        take: limit,
        skip: offset,
      }),
      prisma.queryHistory.count(),
    ]);

    res.json({
      success: true,
      data: {
        items: history,
        total,
        limit,
        offset,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: getErrorMessage(error),
      },
    });
  }
});

export default router;
