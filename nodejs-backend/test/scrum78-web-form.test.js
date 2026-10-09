'use strict';
/** Kiểm thử tiêu chí chấp nhận SCRUM-78 — Biểu mẫu nhúng thu thập lead. */
const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { startApp } = require('./helpers');

const VALID = { full_name: 'Nguyễn Văn An', email: 'an@abc.vn', phone: '0912 345 678', company: 'ABC', interest: 'CRM' };
let t;
beforeEach(async () => { t = await startApp(); });
afterEach(async () => { await t.close(); });

async function createForm(extra = {}) {
  const res = await t.post('/api/forms', { name: 'Form trang chủ', ...extra });
  assert.equal(res.status, 201, JSON.stringify(res.data));
  return res.data;
}
const submit = (key, data = VALID, ip = '1.1.1.1', headers = {}) => t.post(
  `/public/forms/${key}/submit`, data, { 'X-Forwarded-For': ip, ...headers },
);

test('AC78-01 tạo biểu mẫu sinh mã nhúng script & iframe', async () => {
  const form = await createForm();
  assert.match(form.embed.script, new RegExp(`/embed/${form.public_key}\\.js`));
  assert.match(form.embed.iframe, /<iframe/);
  const res = await t.get(`/api/forms/${form.id}/embed-code`);
  assert.equal(res.data.public_key, form.public_key);
});

test('AC78-02 script nhúng render đủ 5 trường + honeypot', async () => {
  const form = await createForm();
  const res = await t.get(`/embed/${form.public_key}.js`);
  assert.equal(res.status, 200);
  assert.match(res.headers.get('content-type'), /javascript/);
  const js = res.data.toString();
  for (const f of ['full_name', 'email', 'phone', 'company', 'interest', 'website_url']) assert.ok(js.includes(f));
  assert.equal((await t.get(`/embed/${form.public_key}/page`)).status, 200);
});

test('AC78-03 gửi thành công tạo lead Mới, đúng nguồn & chiến dịch', async () => {
  const campaignId = t.seedCampaign();
  const form = await createForm({ campaign_id: campaignId });
  assert.equal((await submit(form.public_key)).status, 201);
  const lead = (await t.get('/api/leads')).data.items[0];
  assert.equal(lead.status, 'Mới');
  assert.equal(lead.source, 'web_form');
  assert.equal(lead.form_id, form.id);
  assert.equal(lead.campaign_id, campaignId);
  assert.equal(lead.phone, '0912345678');
});

test('AC78-04 dữ liệu sai báo lỗi từng trường, không tạo lead', async () => {
  const form = await createForm();
  const res = await submit(form.public_key, { full_name: '', email: 'sai', phone: '123' });
  assert.equal(res.status, 422);
  assert.deepEqual(Object.keys(res.data.error.details).sort(), ['email', 'full_name', 'phone']);
  assert.equal(t.countLeads(), 0);
});

test('AC78-05 honeypot chặn bot (trả 201 nhưng không tạo lead)', async () => {
  const form = await createForm();
  assert.equal((await submit(form.public_key, { ...VALID, website_url: 'http://spam' })).status, 201);
  assert.equal(t.countLeads(), 0);
});

test('AC78-06 gửi quá nhanh bị xem là spam', async () => {
  const form = await createForm();
  await submit(form.public_key, { ...VALID, _ts: Date.now() });
  assert.equal(t.countLeads(), 0);
  await submit(form.public_key, { ...VALID, _ts: Date.now() - 10000 }, '2.2.2.2');
  assert.equal(t.countLeads(), 1);
});

test('AC78-07 giới hạn tần suất theo IP', async () => {
  const form = await createForm();
  for (let i = 0; i < 5; i += 1) {
    assert.equal((await submit(form.public_key, { ...VALID, email: `u${i}@abc.vn` })).status, 201);
  }
  const blocked = await submit(form.public_key);
  assert.equal(blocked.status, 429);
  assert.ok(blocked.headers.get('retry-after'));
  assert.equal((await submit(form.public_key, VALID, '9.9.9.9')).status, 201);
});

test('AC78-08 chỉ domain được phép mới gửi được', async () => {
  const form = await createForm({ allowed_domains: ['https://congty.vn'] });
  assert.deepEqual(form.allowed_domains, ['congty.vn']);
  assert.equal((await submit(form.public_key, VALID, '1.1.1.1', { Origin: 'https://evil.com' })).status, 403);
  assert.equal((await submit(form.public_key, VALID, '3.3.3.3', { Origin: 'https://www.congty.vn' })).status, 201);
});

test('AC78-09 biểu mẫu tắt không nhận dữ liệu', async () => {
  const form = await createForm();
  const res = await t.patch(`/api/forms/${form.id}`, { is_active: false });
  assert.equal(res.data.is_active, false);
  assert.equal((await submit(form.public_key)).status, 404);
});

test('AC78-10 validate khi tạo biểu mẫu', async () => {
  const res = await t.post('/api/forms', { name: '', allowed_domains: ['không hợp lệ'], campaign_id: 999 });
  assert.equal(res.status, 422);
  assert.deepEqual(Object.keys(res.data.error.details).sort(), ['allowed_domains', 'campaign_id', 'name']);
});
