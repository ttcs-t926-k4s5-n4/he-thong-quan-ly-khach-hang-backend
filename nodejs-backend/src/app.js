'use strict';
/**
 * Ứng dụng Node.js (không framework) cho epic SCRUM-19 — Lead & Marketing (chỉ backend).
 * Mỗi story là một module trong src/features; module nào có trong nhánh hiện tại thì được nạp,
 * nên từng nhánh feature/SCRUM-xx vẫn chạy riêng được.
 */
const http = require('http');
const path = require('path');
const { JsonStore } = require('./core/db');
const { Router, parseRequestBody, sendJson } = require('./core/http');
const { SlidingWindowLimiter } = require('./core/rateLimiter');
const { ApiError } = require('./core/utils');
const { registerCoreRoutes } = require('./core/leads');

const FEATURE_MODULES = [
  './features/scrum78-web-form',
  './features/scrum79-lead-import',
  './features/scrum80-campaign-tracking',
];

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
  'Access-Control-Allow-Methods': 'GET, POST, PATCH, OPTIONS',
};

function loadConfig(overrides = {}) {
  const env = process.env;
  return {
    DB_PATH: env.DB_PATH || path.join(__dirname, '..', 'data', 'crm_leads.json'),
    TRUST_PROXY: ['1', 'true', 'yes', 'on'].includes(String(env.TRUST_PROXY || '').toLowerCase()),
    PUBLIC_BASE_URL: (env.PUBLIC_BASE_URL || '').replace(/\/$/, ''),
    RATE_LIMIT_PER_FORM: env.RATE_LIMIT_PER_FORM || '5/600', // 5 lần / 10 phút / IP / biểu mẫu
    RATE_LIMIT_PER_IP: env.RATE_LIMIT_PER_IP || '20/3600', // 20 lần / giờ / IP (mọi biểu mẫu)
    MIN_FILL_SECONDS: Number(env.MIN_FILL_SECONDS || 3),
    MAX_IMPORT_ROWS: Number(env.MAX_IMPORT_ROWS || 2000),
    IMPORT_PREVIEW_TTL_MINUTES: Number(env.IMPORT_PREVIEW_TTL_MINUTES || 30),
    MAX_BODY_BYTES: 5 * 1024 * 1024,
    ...overrides,
  };
}

function createApp(overrides = {}) {
  const config = loadConfig(overrides);
  const db = new JsonStore(config.DB_PATH);
  const limiter = new SlidingWindowLimiter();
  const router = new Router();
  registerCoreRoutes(router);

  const features = [];
  for (const modulePath of FEATURE_MODULES) {
    let mod;
    try {
      mod = require(modulePath);
    } catch (err) {
      const missing = err.code === 'MODULE_NOT_FOUND' && err.message.includes(path.basename(modulePath));
      if (missing) continue; // feature chưa có trong nhánh này -> bỏ qua
      throw err;
    }
    mod.register(router);
    features.push(mod.FEATURE);
  }

  router.get('/health', () => ({
    json: { status: 'ok', service: 'crm-lead-marketing (nodejs)', features },
  }));

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    try {
      if (req.method === 'OPTIONS') {
        res.writeHead(204, CORS_HEADERS);
        res.end();
        return;
      }
      const matched = router.match(req.method, url.pathname);
      if (!matched) throw new ApiError(404, 'Không tìm thấy đường dẫn API');
      if (matched.methodNotAllowed) throw new ApiError(405, 'Phương thức HTTP không được hỗ trợ cho đường dẫn này');

      const { body, files } = await parseRequestBody(req, config.MAX_BODY_BYTES);
      const forwarded = config.TRUST_PROXY ? String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() : '';
      const ctx = {
        req,
        db,
        config,
        limiter,
        params: matched.params,
        query: url.searchParams,
        body,
        files,
        headers: req.headers,
        ip: forwarded || req.socket.remoteAddress || 'unknown',
        userId: req.headers['x-user-id'] || null,
        baseUrl: config.PUBLIC_BASE_URL || `http://${req.headers.host}`,
        hostName: url.hostname.toLowerCase(),
      };
      const result = (await matched.handler(ctx)) || {};
      const status = result.status || 200;
      if (result.json !== undefined) {
        sendJson(res, status, result.json, { ...CORS_HEADERS, ...(result.headers || {}) });
      } else {
        res.writeHead(status, { ...CORS_HEADERS, 'Content-Type': result.contentType || 'text/plain; charset=utf-8', ...(result.headers || {}) });
        res.end(result.body || '');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        const payload = { error: { status: err.status, message: err.message } };
        if (err.details) payload.error.details = err.details;
        sendJson(res, err.status, payload, { ...CORS_HEADERS, ...err.headers });
      } else {
        console.error('Lỗi không mong muốn:', err);
        sendJson(res, 500, { error: { status: 500, message: 'Lỗi hệ thống, vui lòng thử lại sau' } }, CORS_HEADERS);
      }
    }
  });

  return { server, db, config, limiter, features };
}

module.exports = { createApp };
