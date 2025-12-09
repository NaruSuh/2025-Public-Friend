import { z } from 'zod';

/**
 * Runtime validation schemas for R-ONE Service methods
 * Provides type safety beyond TypeScript compile-time checks
 */

// Common schemas
export const tableIdSchema = z.string().min(1, 'Table ID cannot be empty');

export const periodCodeSchema = z.enum(['MM', 'QQ', 'YY'], {
  errorMap: () => ({ message: 'Period code must be MM (monthly), QQ (quarterly), or YY (yearly)' }),
});

export const dateIdentifierSchema = z.string().regex(/^\d{6,8}$/, {
  message: 'Date identifier must be in YYYYMM or YYYYMMDD format',
});

export const paginationSchema = z.object({
  pageNo: z.number().int().positive().optional(),
  numOfRows: z.number().int().positive().max(1000).optional(),
});

// GetAvailableStatistics parameters
export const getAvailableStatisticsSchema = z
  .object({
    category: z.string().optional(),
    searchKeyword: z.string().optional(),
  })
  .optional();

// GetKeyStatistics parameters
export const getKeyStatisticsSchema = z.object({
  count: z.number().int().positive().max(100).optional().default(10),
});

// SearchTables parameters
export const searchTablesSchema = z.object({
  keyword: z.string().min(1, 'Search keyword cannot be empty'),
  category: z.string().optional(),
});

// GetTableData parameters
export const getTableDataSchema = z.object({
  tableId: tableIdSchema,
  periodCode: periodCodeSchema.optional(),
  dateIdentifier: dateIdentifierSchema.optional(),
  groupId: z.string().optional(),
  classId: z.string().optional(),
  itemId: z.string().optional(),
  ...paginationSchema.shape,
});

// GetRealEstateIndex parameters
export const getRealEstateIndexSchema = z.object({
  region: z.string().min(1, 'Region cannot be empty'),
  dateIdentifier: dateIdentifierSchema.optional(),
  propertyType: z.enum(['apt', 'detached', 'multi_family', 'land']).optional(),
});

// GetRegionalPrices parameters
export const getRegionalPricesSchema = z.object({
  region: z.string().min(1, 'Region cannot be empty'),
  periodCode: periodCodeSchema.optional(),
  dateIdentifier: dateIdentifierSchema.optional(),
  propertyType: z.enum(['apt', 'detached', 'multi_family', 'land']).optional(),
});

// GetNationalStatistics parameters
export const getNationalStatisticsSchema = z.object({
  periodCode: periodCodeSchema.optional(),
  dateIdentifier: dateIdentifierSchema.optional(),
  category: z.string().optional(),
});

// GetTimeSeriesData parameters
export const getTimeSeriesDataSchema = z.object({
  tableId: tableIdSchema,
  startDate: dateIdentifierSchema,
  endDate: dateIdentifierSchema,
  periodCode: periodCodeSchema.optional(),
});

// Type exports (inferred from schemas)
export type GetAvailableStatisticsParams = z.infer<typeof getAvailableStatisticsSchema>;
export type GetKeyStatisticsParams = z.infer<typeof getKeyStatisticsSchema>;
export type SearchTablesParams = z.infer<typeof searchTablesSchema>;
export type GetTableDataParams = z.infer<typeof getTableDataSchema>;
export type GetRealEstateIndexParams = z.infer<typeof getRealEstateIndexSchema>;
export type GetRegionalPricesParams = z.infer<typeof getRegionalPricesSchema>;
export type GetNationalStatisticsParams = z.infer<typeof getNationalStatisticsSchema>;
export type GetTimeSeriesDataParams = z.infer<typeof getTimeSeriesDataSchema>;
