'use strict';
/** Tiện ích test dùng chung: mỗi test chạy một server riêng, dữ liệu trong RAM. */
const { createApp } = require('../src/app');
const { insertLead } = require('../src/core/leads');
const { nowIso } = require('../src/core/utils');

async function startApp(overrides = {}) {
  const app = createApp({
    DB_PATH: ':memory:',
    TRUST_PROXY: true,
    MIN_FILL_SECONDS: 3,
    RATE_LIMIT_PER_FORM: '5/600',
    RATE_LIMIT_PER_IP: '20/3600',
    ...overrides,
  });
  await new Promise((resolve) => app.server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${app.server.address().port}`;

  async function call(method, path, body, headers = {}) {
    const opts = { method, headers: { ...headers } };
    if (body instanceof FormData) opts.body = body;
    else if (body !== undefined) {
      opts.body = JSON.stringify(body);
      opts.headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(base + path, opts);
    const type = res.headers.get('content-type') || '';
    const data = type.includes('json') ? await res.json() : Buffer.from(await res.arrayBuffer());
    return { status: res.status, headers: res.headers, data };
  }

  return {
    app,
    base,
    db: app.db,
    get: (p, h) => call('GET', p, undefined, h),
    post: (p, b, h) => call('POST', p, b === undefined ? {} : b, h),
    patch: (p, b, h) => call('PATCH', p, b, h),
    close: () => new Promise((resolve) => app.server.close(resolve)),
    seedCampaign(o = {}) {
      const ts = nowIso();
      return app.db.insert('campaigns', {
        name: 'Hội thảo CĐS 2026', channel: 'hoi_thao', budget: 10000000,
        start_date: '2026-01-01', end_date: '2026-12-31', description: null, created_by: null,
        created_at: ts, updated_at: ts, ...o,
      }).id;
    },
    seedLead(o = {}) {
      return insertLead(app.db, { full_name: 'Khách Mẫu', source: 'hoi_thao', ...o }).id;
    },
    countLeads: () => app.db.count('leads'),
  };
}

module.exports = { startApp };
