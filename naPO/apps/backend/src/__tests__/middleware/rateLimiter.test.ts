import { describe, it, expect, beforeEach } from '@jest/globals';
import request from 'supertest';
import express, { Express } from 'express';
import { apiLimiter, queryLimiter, authLimiter } from '@/middleware/rateLimiter';

describe('Rate Limiter Middleware', () => {
  let app: Express;

  beforeEach(() => {
    app = express();
  });

  describe('apiLimiter', () => {
    it('should allow requests under the limit', async () => {
      app.use('/api', apiLimiter);
      app.get('/api/test', (req, res) => res.json({ success: true }));

      const response = await request(app).get('/api/test');
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should block requests over the limit', async () => {
      app.use('/api', apiLimiter);
      app.get('/api/test', (req, res) => res.json({ success: true }));

      // Make 101 requests (limit is 100)
      for (let i = 0; i < 100; i++) {
        await request(app).get('/api/test');
      }

      const response = await request(app).get('/api/test');
      expect(response.status).toBe(429); // Too Many Requests
      expect(response.body.error.code).toBe('TOO_MANY_REQUESTS');
    });
  });

  describe('queryLimiter', () => {
    it('should allow queries under the limit', async () => {
      app.use('/query', queryLimiter);
      app.post('/query', (req, res) => res.json({ success: true }));

      const response = await request(app).post('/query');
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should block queries over the limit', async () => {
      app.use('/query', queryLimiter);
      app.post('/query', (req, res) => res.json({ success: true }));

      // Make 21 requests (limit is 20)
      for (let i = 0; i < 20; i++) {
        await request(app).post('/query');
      }

      const response = await request(app).post('/query');
      expect(response.status).toBe(429);
      expect(response.body.error.code).toBe('QUERY_RATE_LIMIT_EXCEEDED');
    });
  });

  describe('authLimiter', () => {
    it('should allow auth requests under the limit', async () => {
      app.use('/auth', authLimiter);
      app.post('/auth/login', (req, res) => res.json({ success: false }));

      const response = await request(app).post('/auth/login');
      expect(response.status).toBe(200);
    });

    it('should block failed auth attempts over the limit', async () => {
      app.use('/auth', authLimiter);
      app.post('/auth/login', (req, res) => res.status(401).json({ success: false }));

      // Make 6 failed attempts (limit is 5)
      for (let i = 0; i < 5; i++) {
        await request(app).post('/auth/login');
      }

      const response = await request(app).post('/auth/login');
      expect(response.status).toBe(429);
    });
  });
});
