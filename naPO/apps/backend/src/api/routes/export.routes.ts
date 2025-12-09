import { Router, Request, Response } from 'express';
import { CsvExporter } from '@/services/export/csvExporter';

const router = Router();
const csvExporter = new CsvExporter();

// Export data
router.post('/', async (req: Request, res: Response) => {
  try {
    const { data, format, options } = req.body;

    if (!data || !Array.isArray(data)) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Data array is required',
        },
      });
    }

    if (!format) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Export format is required (csv or json)',
        },
      });
    }

    switch (format) {
      case 'csv': {
        const result = await csvExporter.export(data, options);
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="export-${Date.now()}.csv"`);
        return res.send(result.content);
      }

      case 'json': {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="export-${Date.now()}.json"`);
        return res.send(JSON.stringify(data, null, 2));
      }

      default:
        return res.status(400).json({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: `Unsupported format: ${format}. Supported formats: csv, json`,
          },
        });
    }
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
