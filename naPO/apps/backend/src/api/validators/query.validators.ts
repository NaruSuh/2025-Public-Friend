import { body } from 'express-validator';

// Custom sanitizer to remove potentially dangerous patterns
const sanitizeQuery = (value: string): string => {
  if (typeof value !== 'string') return value;
  // Remove HTML tags
  let sanitized = value.replace(/<[^>]*>/g, '');
  // Remove null bytes
  sanitized = sanitized.replace(/\0/g, '');
  // Normalize whitespace
  sanitized = sanitized.replace(/\s+/g, ' ').trim();
  return sanitized;
};

export const parseQueryValidation = [
  body('query')
    .exists()
    .withMessage('Query is required')
    .isString()
    .withMessage('Query must be a string')
    .trim()
    .isLength({ min: 1, max: 1000 })
    .withMessage('Query must be between 1 and 1000 characters')
    .customSanitizer(sanitizeQuery),
];

export const executeQueryValidation = [
  body('parsedQuery')
    .exists()
    .withMessage('Parsed query is required')
    .isObject()
    .withMessage('Parsed query must be an object'),

  body('parsedQuery.intent')
    .exists()
    .withMessage('Intent is required')
    .isIn(['fetch_api', 'crawl_site', 'parse_pdf', 'analyze_data', 'export_data'])
    .withMessage('Invalid intent type'),

  body('parsedQuery.source')
    .exists()
    .withMessage('Source is required')
    .isObject()
    .withMessage('Source must be an object'),

  body('parsedQuery.source.type')
    .exists()
    .withMessage('Source type is required')
    .isIn(['api', 'crawler', 'local', 'unknown'])
    .withMessage('Invalid source type'),
];
