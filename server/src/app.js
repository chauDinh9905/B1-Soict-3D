import express from 'express';
import helmet from 'helmet';
import { pinoHttp } from 'pino-http';
import { randomUUID } from 'node:crypto';
import { config } from './config.js';
import { logger } from './infra/logger.js';
import { query } from './infra/db.js';
import { createSessionMiddleware, absoluteTimeout } from './middleware/session.js';
import { sameOrigin } from './middleware/sameOrigin.js';
import { createLimiters } from './middleware/rateLimit.js';
import { errorHandler } from './middleware/errorHandler.js';
import { loadCurrentUser } from './modules/auth/service.js';
import { authRoutes } from './modules/auth/routes.js';
import { campusRoutes } from './modules/campus/routes.js';
import { buildingRoutes } from './modules/buildings/routes.js';
import { poiRoutes } from './modules/pois/routes.js';
import { feedbackRoutes } from './modules/feedback/routes.js';
import { statsRoutes } from './modules/stats/routes.js';

/** Tạo app nhưng KHÔNG listen – để test gọi thẳng. redis phải đã connect (rate limit nạp script khi tạo). */
export function createApp({ redis }) {
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', config.TRUST_PROXY);     // đứng sau Vercel / host: cần để cookie Secure và req.ip đúng

  // Kiểm tra sức khỏe – đặt trước mọi thứ khác, không cần session.
  app.get('/healthz', (_req, res) => res.json({ ok: true }));              // còn sống (không gọi CSDL)
  app.get('/readyz', async (_req, res) => {                                // sẵn sàng nhận request
    try {
      await query('SELECT 1');
      await redis.ping();
      res.json({ ok: true });
    } catch {
      res.status(503).json({ ok: false });
    }
  });

  app.use(pinoHttp({
    logger,
    genReqId: (req, res) => {
      const id = req.headers['x-request-id'] ?? randomUUID();
      res.setHeader('x-request-id', id);
      return id;
    },
  }));
  app.use(helmet());
  app.use(express.json({ limit: '20kb' }));
  app.use('/api', sameOrigin);
  app.use(createSessionMiddleware(redis));
  app.use(absoluteTimeout);
  app.use(loadCurrentUser);

  const limiters = createLimiters(redis);
  app.get('/api/health', (_req, res) => res.json({ ok: true }));            // giữ cho tương thích cũ
  app.use('/api/auth', authRoutes({ redis, limiters }));
  app.use('/api/campus', campusRoutes());
  app.use('/api/buildings', buildingRoutes());
  app.use('/api/pois', poiRoutes());
  app.use('/api/feedback', feedbackRoutes());
  app.use('/api/stats', statsRoutes());

  app.use('/api', (_req, res) => res.status(404).json({ error: 'Không có đường dẫn này', code: 'NOT_FOUND' }));
  app.use(errorHandler);
  return app;
}
