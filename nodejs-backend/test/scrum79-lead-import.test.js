'use strict';
/** Kiểm thử tiêu chí chấp nhận SCRUM-79 — Nhập tay & nhập Excel hàng loạt. */
const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { startApp } = require('./helpers');
const { writeXlsx, readXlsx } = require('../src/core/xlsx');

const HEADERS = ['Họ tên*', 'Email', 'Số điện thoại', 'Công ty', 'Nhu cầu quan tâm', 'Nguồn', 'Chi tiết nguồn'];
let t;
beforeEach(async () => { t = await startApp(); });
afterEach(async () => { await t.close(); });

function upload(rows, fields = {}, filename = 'hoi-thao.xlsx', raw = null) {
  const fd = new FormData();
  const data = raw || writeXlsx([{ name: 'Danh sách lead', rows }]);
  fd.append('file', new Blob([data]), filename);
  for (const [k, v] of Object.entries(fields)) fd.append(k, String(v));
  return t.post('/api/leads/import/preview', fd);
}

test('AC79-01 nhập tay lead từ sự kiện / danh thiếp', async () => {
  const res = await t.post('/api/leads', {
    full_name: 'Trần Thị Bình', phone: '+84 912 000 111', source: 'Danh thiếp', source_detail: 'Expo 2026',
  }, { 'X-User-Id': 'mkt01' });
  assert.equal(res.status, 201, JSON.stringify(res.data));
  assert.equal(res.data.status, 'Mới');
  assert.equal(res.data.source, 'danh_thiep');
  assert.equal(res.data.phone, '0912000111');
  assert.equal(res.data.created_by, 'mkt01');
});

test('AC79-02 nhập tay bắt buộc có nguồn hợp lệ', async () => {
  const noSource = await t.post('/api/leads', { full_name: 'A', email: 'a@x.vn' });
  assert.equal(noSource.status, 422);
  assert.ok(noSource.data.error.details.source);
  assert.equal((await t.post('/api/leads', { full_name: 'A', email: 'a@x.vn', source: 'web_form' })).status, 422);
});

test('AC79-03 cần ít nhất email hoặc SĐT', async () => {
  const res = await t.post('/api/leads', { full_name: 'A', source: 'su_kien' });
  assert.equal(res.status, 422);
  assert.ok(res.data.error.details.contact);
});

test('AC79-04 cảnh báo trùng lead', async () => {
  await t.post('/api/leads', { full_name: 'A', email: 'a@x.vn', source: 'su_kien' });
  assert.equal((await t.post('/api/leads', { full_name: 'B', email: 'A@X.VN', source: 'su_kien' })).status, 409);
  assert.equal((await t.post('/api/leads', {
    full_name: 'B', email: 'a@x.vn', source: 'su_kien', allow_duplicate: true,
  })).status, 201);
});

test('AC79-05 tải tệp mẫu', async () => {
  const res = await t.get('/api/leads/import/template');
  assert.equal(res.status, 200);
  const rows = readXlsx(res.data);
  assert.equal(rows[0][0], 'Họ tên*');
  assert.ok(rows[0].includes('Nguồn'));
});

test('AC79-06 xem trước báo lỗi theo từng dòng, không ghi DB', async () => {
  t.seedLead({ full_name: 'Cũ', email: 'cu@x.vn' });
  const res = await upload([
    HEADERS,
    ['Lê Văn C', 'c@x.vn', '912345678', 'C Corp', '', 'Hội thảo', 'HT CĐS'],
    ['', 'd@x.vn', '', '', '', 'Hội thảo', ''],
    ['Phạm E', 'sai-email', '', '', '', 'Hội thảo', ''],
    ['Võ F', 'c@x.vn', '', '', '', 'Hội thảo', ''],
    ['Đỗ G', 'cu@x.vn', '', '', '', 'Hội thảo', ''],
    ['Hồ H', 'h@x.vn', '', '', '', 'Bay từ trên trời', ''],
  ]);
  assert.equal(res.status, 201, JSON.stringify(res.data));
  assert.deepEqual([res.data.total_rows, res.data.valid_rows, res.data.error_rows], [6, 1, 5]);
  assert.deepEqual([...new Set(res.data.errors.map((e) => e.row_number))].sort(), [3, 4, 5, 6, 7]);
  assert.equal(res.data.rows[0].data.phone, '0912345678');
  assert.equal(t.countLeads(), 1);
});

test('AC79-07 xác nhận chỉ nhập dòng hợp lệ, mọi lead có nguồn', async () => {
  const campaignId = t.seedCampaign();
  const preview = (await upload([
    ['Họ tên', 'Email', 'SĐT', 'Nguồn'],
    ['A1', 'a1@x.vn', '', ''],
    ['A2', 'a2@x.vn', '0988000111', 'Sự kiện'],
    ['A3', 'sai', '', ''],
  ], { default_source: 'hoi_thao', source_detail: 'Hội thảo 10/10', campaign_id: campaignId })).data;
  assert.equal(preview.valid_rows, 2);
  const commit = await t.post(`/api/leads/import/${preview.preview_id}/commit`, {});
  assert.equal(commit.status, 201, JSON.stringify(commit.data));
  assert.equal(commit.data.imported_count, 2);
  assert.equal(commit.data.skipped_count, 1);
  const leads = (await t.get(`/api/leads?import_batch_id=${preview.preview_id}`)).data.items;
  assert.deepEqual(new Set(leads.map((l) => l.source)), new Set(['hoi_thao', 'su_kien']));
  assert.ok(leads.every((l) => l.campaign_id === campaignId && l.status === 'Mới'));
  assert.equal((await t.post(`/api/leads/import/${preview.preview_id}/commit`, {})).status, 409);
});

test('AC79-08 không có nguồn thì dòng bị lỗi', async () => {
  const res = await upload([['Họ tên', 'Email'], ['A', 'a@x.vn']]);
  assert.equal(res.data.error_rows, 1);
  assert.equal(res.data.rows[0].errors[0].field, 'source');
});

test('AC79-09 all_or_nothing không nhập khi còn lỗi', async () => {
  const res = await upload([['Họ tên', 'Email'], ['A', 'a@x.vn'], ['B', 'sai']], { default_source: 'su_kien' });
  const commit = await t.post(`/api/leads/import/${res.data.id}/commit`, { mode: 'all_or_nothing' });
  assert.equal(commit.status, 422);
  assert.equal(t.countLeads(), 0);
});

test('AC79-10 kiểm tra định dạng tệp & cột', async () => {
  assert.equal((await upload(null, {}, 'a.pdf', Buffer.from('abc'))).status, 400);
  assert.equal((await upload([['Email'], ['a@x.vn']])).status, 400);
  assert.equal((await upload([HEADERS])).status, 400);
});

test('AC79-11 hỗ trợ CSV', async () => {
  const csv = Buffer.from('\uFEFFHọ tên;Email;Nguồn\nNguyễn A;a@x.vn;Giới thiệu\n', 'utf8');
  const res = await upload(null, {}, 'ds.csv', csv);
  assert.equal(res.status, 201, JSON.stringify(res.data));
  assert.equal(res.data.rows[0].data.source, 'gioi_thieu');
});
