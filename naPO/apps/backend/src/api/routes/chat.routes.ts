import { Router } from 'express';
import type { Router as IRouter } from 'express';
import { body, validationResult } from 'express-validator';
import { ChatService } from '@/services/chat/chatService';
import { env } from '@/config/env';

const router: IRouter = Router();
const chatService = new ChatService();

router.post(
  '/',
  body('message').isString().trim().notEmpty().withMessage('message is required'),
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ message: 'Invalid request', errors: errors.array() });
      }
      if (!env.GEMINI_API_KEY) {
        return res.status(500).json({ message: 'GEMINI_API_KEY not configured' });
      }

      const { message, sessionId } = req.body as { message: string; sessionId?: string };
      const response = await chatService.chat(message, sessionId);
      return res.json(response);
    } catch (error) {
      return next(error);
    }
  }
);

export default router;
