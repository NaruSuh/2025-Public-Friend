import { Router, Request, Response } from 'express';
import { prisma } from '@/lib/prisma';

const router = Router();

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
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

export default router;
