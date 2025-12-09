import morgan from 'morgan';
import { createLogger, format, transports } from 'winston';

// Winston logger instance
export const logger = createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: format.combine(
    format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    format.errors({ stack: true }),
    format.splat(),
    format.json()
  ),
  defaultMeta: { service: 'napo-backend' },
  transports: [
    // Write all logs to console
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.printf(({ timestamp, level, message, ...meta }) => {
          return `${timestamp} [${level}]: ${message} ${
            Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''
          }`;
        })
      ),
    }),
    // Write all logs with level `error` and below to `error.log`
    new transports.File({ filename: 'logs/error.log', level: 'error' }),
    // Write all logs to `combined.log`
    new transports.File({ filename: 'logs/combined.log' }),
  ],
});

// Morgan middleware with Winston stream
export const morganMiddleware = morgan(
  process.env.NODE_ENV === 'production'
    ? 'combined' // Standard Apache combined log output
    : 'dev', // Colored output for development
  {
    stream: {
      write: (message: string) => {
        // Send morgan output to Winston
        logger.http(message.trim());
      },
    },
  }
);
