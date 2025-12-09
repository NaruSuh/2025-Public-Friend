import express, { Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import dotenv from 'dotenv';
import { initSentry, Sentry } from './config/sentry';
import apiRoutes from './api/routes';
import { errorHandler, notFoundHandler } from './api/middlewares/errorHandler';
import { apiLimiter } from './middleware/rateLimiter';
import { morganMiddleware, logger } from './config/logger';

// Load environment variables FIRST
dotenv.config();

// Initialize Sentry BEFORE creating Express app
initSentry();

const app = express();
const PORT = process.env.PORT || 3001;

// Sentry request handler must be the first middleware
if (Sentry && (Sentry as any).Handlers) {
  app.use((Sentry as any).Handlers.requestHandler());
  app.use((Sentry as any).Handlers.tracingHandler());
}

// Security & Performance Middleware
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", 'data:', 'https:'],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
      },
    },
    crossOriginEmbedderPolicy: false, // Required for some APIs
    crossOriginResourcePolicy: { policy: 'cross-origin' },
    hsts: {
      maxAge: 31536000, // 1 year
      includeSubDomains: true,
      preload: true,
    },
    noSniff: true,
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
    xssFilter: true,
  })
);
app.use(
  compression({
    filter: (req: Request, res: Response): boolean => {
      if (req.headers['x-no-compression']) {
        return false;
      }
      return compression.filter(req, res);
    },
    level: 6,
    threshold: 1024, // Only compress responses > 1KB
  })
);

// Logging
app.use(morganMiddleware);

// CORS
app.use(
  cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true,
  })
);

// Body parsing
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting for all API routes
app.use('/api', apiLimiter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API Routes
app.use('/api/v1', apiRoutes);

// 404 Handler
app.use(notFoundHandler);

// Sentry error handler must be before other error handlers
if (Sentry && (Sentry as any).Handlers) {
  app.use((Sentry as any).Handlers.errorHandler());
}

// Error handler
app.use(errorHandler);

app.listen(PORT, () => {
  logger.info(`🚀 naPO Backend server running on http://localhost:${PORT}`);
  logger.info(`📚 API: http://localhost:${PORT}/api/v1`);
  logger.info(`✅ Compression enabled`);
  logger.info(`✅ Rate limiting active`);
  logger.info(`✅ HTTP logging enabled`);
});

export default app;
