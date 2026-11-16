import pino from 'pino';
import { config } from '../config.js';

// Log dạng JSON. Các trường dưới đây KHÔNG BAO GIỜ được ghi ra log.
export const logger = pino({
  level: config.NODE_ENV === 'test' ? 'silent' : config.LOG_LEVEL,
  redact: {
    paths: [
      'req.headers.cookie',
      'req.headers.authorization',
      'res.headers["set-cookie"]',
      '*.password',
      '*.currentPassword',
      '*.newPassword',
      '*.token',
      '*.credential',
    ],
    censor: '[đã che]',
  },
});
