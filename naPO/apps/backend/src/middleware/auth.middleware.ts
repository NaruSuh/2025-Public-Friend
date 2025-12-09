import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email?: string;
        role?: string;
      };
    }
  }
}

/**
 * Get JWT secret from environment
 */
function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET;

  if (!secret) {
    console.warn(
      'WARNING: JWT_SECRET not set in environment. Using default secret. ' +
      'This is insecure for production use. Please set JWT_SECRET environment variable.'
    );
    return 'default-jwt-secret-change-in-production';
  }

  return secret;
}

/**
 * Generate JWT token
 */
export function generateToken(payload: { id: string; email?: string; role?: string }): string {
  const secret = getJwtSecret();
  return jwt.sign(payload, secret, {
    expiresIn: '7d', // Token expires in 7 days
  });
}

/**
 * Verify JWT token
 */
export function verifyToken(token: string): any {
  const secret = getJwtSecret();
  try {
    return jwt.verify(token, secret);
  } catch (error) {
    return null;
  }
}

/**
 * Authentication middleware - checks for valid JWT token
 * Can be used to protect routes that require authentication
 */
export function authenticate(req: Request, res: Response, next: NextFunction): void {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'No authentication token provided',
        },
      });
      return;
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify token
    const decoded = verifyToken(token);

    if (!decoded) {
      res.status(401).json({
        success: false,
        error: {
          code: 'INVALID_TOKEN',
          message: 'Invalid or expired authentication token',
        },
      });
      return;
    }

    // Attach user info to request
    req.user = {
      id: decoded.id,
      email: decoded.email,
      role: decoded.role,
    };

    next();
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: {
        code: 'AUTH_ERROR',
        message: 'Authentication error',
      },
    });
  }
}

/**
 * Optional authentication middleware - attaches user if token is valid, but doesn't require it
 */
export function optionalAuth(req: Request, res: Response, next: NextFunction): void {
  try {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const decoded = verifyToken(token);

      if (decoded) {
        req.user = {
          id: decoded.id,
          email: decoded.email,
          role: decoded.role,
        };
      }
    }

    next();
  } catch (error) {
    // Ignore errors in optional auth
    next();
  }
}

/**
 * Role-based authorization middleware
 */
export function authorize(...allowedRoles: string[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Authentication required',
        },
      });
      return;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(req.user.role || '')) {
      res.status(403).json({
        success: false,
        error: {
          code: 'FORBIDDEN',
          message: 'Insufficient permissions',
        },
      });
      return;
    }

    next();
  };
}

/**
 * Development mode bypass - allows access without authentication in development
 */
export function devAuth(req: Request, res: Response, next: NextFunction): void {
  if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test') {
    // In development, create a mock user
    req.user = {
      id: 'dev-user',
      email: 'dev@localhost',
      role: 'admin',
    };
    next();
  } else {
    // In production, require real authentication
    authenticate(req, res, next);
  }
}
