import { body, param } from 'express-validator';

export const startCrawlValidation = [
  body('crawlerType')
    .exists()
    .withMessage('Crawler type is required')
    .isIn(['nec_library', 'bigkinds', 'manifesto', 'custom'])
    .withMessage('Invalid crawler type'),

  body('options').optional().isObject().withMessage('Options must be an object'),

  body('options.url').optional().isURL().withMessage('Invalid URL format'),

  body('options.maxPages')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Max pages must be between 1 and 1000'),
];

export const getJobStatusValidation = [
  param('jobId')
    .exists()
    .withMessage('Job ID is required')
    .isString()
    .withMessage('Job ID must be a string')
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('Invalid job ID format'),
];
