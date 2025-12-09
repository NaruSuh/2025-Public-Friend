import { body } from 'express-validator';

export const parseFileValidation = [
  body('parserType')
    .exists()
    .withMessage('Parser type is required')
    .isIn(['pymupdf', 'clova_ocr', 'google_vision', 'dolphin'])
    .withMessage('Invalid parser type'),

  body('options').optional().isObject().withMessage('Options must be an object'),

  body('options.pageRange').optional().isObject().withMessage('Page range must be an object'),

  body('options.pageRange.start')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Start page must be >= 1'),

  body('options.pageRange.end').optional().isInt({ min: 1 }).withMessage('End page must be >= 1'),
];
