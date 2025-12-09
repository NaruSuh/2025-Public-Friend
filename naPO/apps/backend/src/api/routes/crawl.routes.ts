import { Router, Request, Response } from 'express';
import { CrawlerFactory } from '@/services/crawler/crawlerFactory';
import { CrawlerType } from '@/types/crawler.types';
import { prisma } from '@/lib/prisma';
import { requireCrawling } from '@/middleware/featureFlag.middleware';
import { logger } from '@/config/logger';

const router = Router();

// Start a crawl job
router.post('/', requireCrawling, async (req: Request, res: Response) => {
  try {
    const { crawlerType, options } = req.body;

    if (!crawlerType) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'crawlerType is required',
        },
      });
    }

    // Check if crawler is available before creating job
    const isAvailable = await CrawlerFactory.isAvailable(crawlerType as CrawlerType);
    if (!isAvailable) {
      return res.status(503).json({
        success: false,
        error: {
          code: 'SERVICE_UNAVAILABLE',
          message: `Crawler type '${crawlerType}' is not yet implemented or unavailable`,
        },
      });
    }

    // Create job in database
    const job = await prisma.dataJob.create({
      data: {
        jobType: 'CRAWL',
        status: 'PENDING',
        inputParams: {
          crawlerType,
          options,
        },
      },
    });

    // Run crawler asynchronously with timeout and resource management
    (async () => {
      try {
        // Update job status to RUNNING and set startedAt
        await prisma.dataJob.update({
          where: { id: job.id },
          data: {
            status: 'RUNNING',
            startedAt: new Date(),
          },
        });

        const crawler = CrawlerFactory.create(crawlerType as CrawlerType);

        // Add timeout to prevent hanging crawls
        const result = await Promise.race([
          crawler.crawl(options || {}),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Crawl timeout: exceeded 10 minutes')), 600000)
          ),
        ]) as any;

        // Save crawled data records
        if (result.items && Array.isArray(result.items)) {
          await prisma.dataRecord.createMany({
            data: result.items.map((item: any) => ({
              jobId: job.id,
              rawData: item.data || item,
              sourceUrl: item.url,
              sourceType: 'crawler',
              tags: item.tags || [],
            })),
          });
        }

        // Update job status to completed
        await prisma.dataJob.update({
          where: { id: job.id },
          data: {
            status: 'COMPLETED',
            resultCount: result.items?.length || 0,
            completedAt: new Date(),
          },
        });
      } catch (error: any) {
        logger.error(`Crawl job ${job.id} failed:`, { error: error.message });

        // Update job status to failed
        await prisma.dataJob.update({
          where: { id: job.id },
          data: {
            status: 'FAILED',
            errorMessage: error.message || 'Unknown error',
            completedAt: new Date(),
          },
        });
      }
    })().catch((err) => {
      logger.error(`Unhandled error in crawl job ${job.id}:`, { error: err.message });
    });

    return res.json({
      success: true,
      data: {
        jobId: job.id,
        status: job.status,
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

// Get crawl job status
router.get('/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;

    const job = await prisma.dataJob.findUnique({
      where: { id: jobId },
      include: {
        _count: {
          select: { dataRecords: true },
        },
      },
    });

    if (!job) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'NOT_FOUND',
          message: 'Job not found',
        },
      });
    }

    return res.json({
      success: true,
      data: {
        id: job.id,
        jobType: job.jobType,
        status: job.status,
        resultCount: job.resultCount || job._count.dataRecords,
        errorMessage: job.errorMessage,
        createdAt: job.createdAt,
        completedAt: job.completedAt,
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

export default router;
