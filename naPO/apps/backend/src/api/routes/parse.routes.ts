import { Router, Request, Response } from 'express';
import multer from 'multer';
import { ParserFactory } from '@/services/parser/parserFactory';
import { ParserType } from '@/types/parser.types';
import { requireOCRParsing } from '@/middleware/featureFlag.middleware';

const router = Router();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed'));
    }
  },
});

// Parse a PDF file
router.post('/', requireOCRParsing, upload.single('file'), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { parserId, options } = req.body;
    const parsedOptions = options ? JSON.parse(options) : {};

    let parser;
    if (parserId) {
      // Check if the requested parser is available
      const availableParsers = await ParserFactory.getAvailableParsers();
      if (!availableParsers.includes(parserId as ParserType)) {
        return res.status(503).json({
          success: false,
          error: {
            code: 'SERVICE_UNAVAILABLE',
            message: `Parser '${parserId}' is not yet implemented or unavailable`,
            availableParsers,
          },
        });
      }
      parser = ParserFactory.create(parserId as ParserType);
    } else {
      // Auto-select best parser
      parser = await ParserFactory.selectBestParser(req.file.buffer);
    }

    const result = await parser.parse(req.file.buffer, parsedOptions);

    return res.json({
      success: true,
      data: result,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

// Get available parsers
router.get('/parsers', async (req: Request, res: Response) => {
  try {
    const available = await ParserFactory.getAvailableParsers();

    return res.json({
      success: true,
      data: available,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
