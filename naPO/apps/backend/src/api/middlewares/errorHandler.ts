/**
 * 전역 에러 핸들링 미들웨어
 *
 * Express 애플리케이션의 모든 에러를 중앙에서 처리합니다.
 * JSON 파싱 에러, Prisma 데이터베이스 에러, 일반 API 에러를 구분하여 처리합니다.
 *
 * @module api/middlewares/errorHandler
 */
import { Request, Response, NextFunction, RequestHandler } from 'express';
import { Prisma } from '@prisma/client';
import { logger } from '@/config/logger';

/**
 * API 에러 인터페이스
 * 표준 Error를 확장하여 HTTP 상태 코드와 에러 코드를 포함합니다.
 */
export interface ApiError extends Error {
  /** HTTP 상태 코드 */
  statusCode?: number;
  /** 에러 식별 코드 (예: 'VALIDATION_ERROR', 'NOT_FOUND') */
  code?: string;
  /** 에러 타입 */
  type?: string;
}

// Check if error is a JSON parsing error
function isJsonParseError(err: any): boolean {
  return err instanceof SyntaxError && 'body' in err;
}

// Check if error is a validation error from express-validator
function isValidationError(err: any): boolean {
  return err.type === 'entity.parse.failed' || err.type === 'charset.unsupported';
}

function isPrismaError(err: any): err is Prisma.PrismaClientKnownRequestError {
  return err instanceof Prisma.PrismaClientKnownRequestError;
}

function handlePrismaError(err: Prisma.PrismaClientKnownRequestError): {
  statusCode: number;
  code: string;
  message: string;
} {
  switch (err.code) {
    case 'P2002':
      return {
        statusCode: 409,
        code: 'DUPLICATE_ENTRY',
        message: 'A record with this value already exists',
      };
    case 'P2025':
      return {
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'The requested record was not found',
      };
    case 'P2003':
      return {
        statusCode: 400,
        code: 'INVALID_REFERENCE',
        message: 'Invalid reference to related record',
      };
    case 'P2014':
      return {
        statusCode: 400,
        code: 'INVALID_RELATION',
        message: 'The change would violate a required relation',
      };
    default:
      return {
        statusCode: 500,
        code: 'DATABASE_ERROR',
        message: 'A database error occurred',
      };
  }
}

export function errorHandler(
  err: ApiError | Prisma.PrismaClientKnownRequestError,
  req: Request,
  res: Response,
  next: NextFunction
) {
  // Log error with appropriate level
  const isClientError = isJsonParseError(err) || isValidationError(err);
  if (isClientError) {
    logger.warn('[Client Error]', {
      message: err.message,
      path: req.path,
      method: req.method,
    });
  } else {
    logger.error('[Error]', {
      message: err.message,
      stack: err.stack,
      path: req.path,
      method: req.method,
    });
  }

  let statusCode: number;
  let code: string;
  let message: string;

  // Handle JSON parsing errors (Invalid JSON body)
  if (isJsonParseError(err)) {
    statusCode = 400;
    code = 'INVALID_JSON';
    message = 'Invalid JSON in request body. Please check your request format.';
  }
  // Handle Prisma errors
  else if (isPrismaError(err)) {
    const prismaError = handlePrismaError(err);
    statusCode = prismaError.statusCode;
    code = prismaError.code;
    message = prismaError.message;
  }
  // Handle regular API errors
  else {
    statusCode = err.statusCode || 500;
    code = err.code || 'INTERNAL_ERROR';
    message = err.message || 'An unexpected error occurred';

    // Sanitize message for production (hide implementation details)
    if (process.env.NODE_ENV === 'production' && statusCode === 500) {
      message = 'An internal server error occurred. Please try again later.';
    }
  }

  res.status(statusCode).json({
    success: false,
    error: {
      code,
      message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    },
  });
}

export function notFoundHandler(req: Request, res: Response) {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
    },
  });
}

/**
 * API 에러를 생성합니다.
 *
 * @param message - 에러 메시지
 * @param statusCode - HTTP 상태 코드
 * @param code - 에러 코드 (선택)
 * @returns 생성된 ApiError 객체
 *
 * @example
 * ```typescript
 * throw createApiError('User not found', 404, 'USER_NOT_FOUND');
 * ```
 */
export function createApiError(message: string, statusCode: number, code?: string): ApiError {
  const error: ApiError = new Error(message);
  error.statusCode = statusCode;
  error.code = code;
  return error;
}

/**
 * 비동기 라우트 핸들러를 래핑하여 에러를 자동으로 next()에 전달합니다.
 * try-catch 보일러플레이트를 제거합니다.
 *
 * @param fn - 비동기 라우트 핸들러 함수
 * @returns 에러 처리가 포함된 RequestHandler
 *
 * @example
 * ```typescript
 * // 기존 방식 (반복적인 try-catch)
 * router.get('/users', async (req, res, next) => {
 *   try {
 *     const users = await getUsers();
 *     res.json(users);
 *   } catch (error) {
 *     next(error);
 *   }
 * });
 *
 * // asyncHandler 사용 (깔끔한 코드)
 * router.get('/users', asyncHandler(async (req, res) => {
 *   const users = await getUsers();
 *   res.json(users);
 * }));
 * ```
 */
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>
): RequestHandler {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
