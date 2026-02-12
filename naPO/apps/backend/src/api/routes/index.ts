import { Router } from 'express';
import type { Router as IRouter } from 'express';
import authRoutes from './auth.routes';
import queryRoutes from './query.routes';
import sourcesRoutes from './sources.routes';
import crawlRoutes from './crawl.routes';
import parseRoutes from './parse.routes';
import exportRoutes from './export.routes';
import historyRoutes from './history.routes';
import chatRoutes from './chat.routes';
import documentsRoutes from './documents.routes';

const router: IRouter = Router();

// Public routes (no authentication required)
router.use('/auth', authRoutes);

// Protected routes (with optional authentication)
// In development mode, these routes work without authentication
// In production, uncomment the authenticate middleware to require authentication
router.use('/query', queryRoutes);
router.use('/sources', sourcesRoutes);
router.use('/crawl', crawlRoutes);
router.use('/parse', parseRoutes);
router.use('/export', exportRoutes);
router.use('/history', historyRoutes);
router.use('/chat', chatRoutes);
router.use('/documents', documentsRoutes);

export default router;
