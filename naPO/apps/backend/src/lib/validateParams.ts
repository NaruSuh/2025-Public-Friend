import { z, ZodError } from 'zod';

/**
 * Generic parameter validation helper
 * Validates input parameters against a Zod schema and returns validated data
 */

export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly errors: z.ZodIssue[]
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Validate parameters against a Zod schema
 * Throws ValidationError if validation fails
 */
export function validateParams<T>(schema: z.ZodSchema<T>, params: unknown): T {
  try {
    return schema.parse(params);
  } catch (error) {
    if (error instanceof ZodError) {
      const errorMessages = error.errors.map((err) => `${err.path.join('.')}: ${err.message}`);
      throw new ValidationError(
        `Parameter validation failed: ${errorMessages.join(', ')}`,
        error.errors
      );
    }
    throw error;
  }
}

/**
 * Validate parameters and return result with success flag
 * Returns { success: true, data } or { success: false, error }
 */
export function validateParamsSafe<T>(
  schema: z.ZodSchema<T>,
  params: unknown
): { success: true; data: T } | { success: false; error: ValidationError } {
  try {
    const data = validateParams(schema, params);
    return { success: true, data };
  } catch (error) {
    if (error instanceof ValidationError) {
      return { success: false, error };
    }
    throw error;
  }
}

/**
 * Usage example:
 *
 * import { validateParams } from '@/lib/validateParams';
 * import { getTableDataSchema } from '@/services/api/schemas/roneServiceSchemas';
 *
 * async function getTableData(params: unknown) {
 *   const validated = validateParams(getTableDataSchema, params);
 *   // Now 'validated' is type-safe and runtime-validated
 *   return await fetchData(validated);
 * }
 */
