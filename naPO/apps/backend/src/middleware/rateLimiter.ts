import rateLimit from 'express-rate-limit';

/**
 * General API rate limiter
 * 15 minutes window, max 100 requests
 */
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    success: false,
    error: {
      code: 'TOO_MANY_REQUESTS',
      message: 'Too many requests from this IP, please try again after 15 minutes',
    },
  },
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});

/**
 * Strict rate limiter for query execution
 * 5 minutes window, max 20 queries
 */
export const queryLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 20, // Limit each IP to 20 queries per 5 minutes
  message: {
    success: false,
    error: {
      code: 'QUERY_RATE_LIMIT_EXCEEDED',
      message: 'Too many queries. Please slow down and try again later.',
    },
  },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Very strict rate limiter for authentication endpoints
 * 15 minutes window, max 5 attempts
 */
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // Only 5 login attempts per 15 minutes
  skipSuccessfulRequests: true, // Don't count successful requests
  message: {
    success: false,
    error: {
      code: 'AUTH_RATE_LIMIT_EXCEEDED',
      message: 'Too many authentication attempts. Please try again after 15 minutes.',
    },
  },
});
