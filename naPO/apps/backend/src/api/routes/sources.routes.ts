import { Router, Request, Response } from 'express';
import { prisma } from '@/lib/prisma';

const router = Router();

// Get all API sources with their keys
router.get('/apis', async (req: Request, res: Response) => {
  try {
    const sources = await prisma.apiSource.findMany({
      include: {
        apiKeys: {
          select: {
            id: true,
            label: true,
            isActive: true,
            createdAt: true,
            expiresAt: true,
            // Don't send actual key value for security
          },
        },
      },
      orderBy: { displayName: 'asc' },
    });

    return res.json({
      success: true,
      data: sources,
    });
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message,
      },
    });
  }
});

// Get single API source
router.get('/apis/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const source = await prisma.apiSource.findUnique({
      where: { id },
      include: {
        apiKeys: {
          select: {
            id: true,
            label: true,
            isActive: true,
            createdAt: true,
            expiresAt: true,
          },
        },
      },
    });

    if (!source) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'NOT_FOUND',
          message: 'API source not found',
        },
      });
    }

    return res.json({
      success: true,
      data: source,
    });
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message,
      },
    });
  }
});

// Add or update API key for a source
router.post('/apis/:id/keys', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { keyValue, label } = req.body;

    if (!keyValue) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'keyValue is required',
        },
      });
    }

    const source = await prisma.apiSource.findUnique({ where: { id } });
    if (!source) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'NOT_FOUND',
          message: 'API source not found',
        },
      });
    }

    const apiKey = await prisma.apiKey.create({
      data: {
        sourceId: source.id,
        keyValue,
        label: label || 'Default Key',
        isActive: true,
      },
    });

    return res.json({
      success: true,
      data: {
        id: apiKey.id,
        label: apiKey.label,
        isActive: apiKey.isActive,
        createdAt: apiKey.createdAt,
      },
    });
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message,
      },
    });
  }
});

// Toggle API key active status
router.patch('/apis/:sourceId/keys/:keyId', async (req: Request, res: Response) => {
  try {
    const { keyId } = req.params;
    const { isActive } = req.body;

    const apiKey = await prisma.apiKey.update({
      where: { id: keyId },
      data: { isActive },
    });

    return res.json({
      success: true,
      data: {
        id: apiKey.id,
        isActive: apiKey.isActive,
      },
    });
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message,
      },
    });
  }
});

// Delete API key
router.delete('/apis/:sourceId/keys/:keyId', async (req: Request, res: Response) => {
  try {
    const { keyId } = req.params;

    await prisma.apiKey.delete({
      where: { id: keyId },
    });

    return res.json({
      success: true,
      message: 'API key deleted',
    });
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message,
      },
    });
  }
});

export default router;
