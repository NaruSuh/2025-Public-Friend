import { Router } from 'express';
import type { Router as IRouter } from 'express';
import authRoutes from './auth.routes.js';
import queryRoutes from './query.routes.js';
import sourcesRoutes from './sources.routes.js';
import crawlRoutes from './crawl.routes.js';
import parseRoutes from './parse.routes.js';
import exportRoutes from './export.routes.js';
import historyRoutes from './history.routes.js';

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

export default router;
