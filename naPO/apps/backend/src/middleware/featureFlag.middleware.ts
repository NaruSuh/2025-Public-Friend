import { Request, Response, NextFunction } from 'express';
import { env } from '@/config/env';

/**
 * Feature flag middleware - checks if a feature is enabled
 */
export function requireFeature(featureName: keyof typeof env) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const isEnabled = env[featureName];

    if (!isEnabled) {
      res.status(503).json({
        success: false,
        error: {
          code: 'FEATURE_DISABLED',
          message: `Feature '${featureName}' is currently disabled`,
        },
      });
      return;
    }

    next();
  };
}

/**
 * Check if natural language query feature is enabled
 */
export const requireNLQuery = requireFeature('ENABLE_NL_QUERY');

/**
 * Check if OCR parsing feature is enabled
 */
export const requireOCRParsing = requireFeature('ENABLE_OCR_PARSING');

/**
 * Check if crawling feature is enabled
 */
export const requireCrawling = requireFeature('ENABLE_CRAWLING');
