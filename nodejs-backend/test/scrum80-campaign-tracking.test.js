'use strict';
/** Kiểm thử tiêu chí chấp nhận SCRUM-80 — Theo dõi lead theo chiến dịch & doanh thu. */
const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { startApp } = require('./helpers');

const CAMPAIGN = { name: 'Facebook Ads Q4', channel: 'facebook', budget: 20000000, start_date: '2026-10-01', end_date: '2026-12-31' };
let t;
beforeEach(async () => { t = await startApp(); });
afterEach(async () => { await t.close(); });

async function createCampaign(extra = {}) {
  const res = await t.post('/api/campaigns', { ...CAMPAIGN, ...extra });
  assert.equal(res.status, 201, JSON.stringify(res.data));
  return res.data;
}
async function convert(leadId, body = {}) {
  return (await t.post(`/api/leads/${leadId}/convert`, body)).data.opportunity;
}

test('AC80-01 khai báo chiến dịch đầy đủ', async () => {
  const c = await createCampaign();
  assert.equal(c.budget, 20000000);
  assert.equal(c.channel_label, 'Facebook');
  assert.ok(['Sắp chạy', 'Đang chạy', 'Đã kết thúc'].includes(c.status));
});

test('AC80-02 validate chiến dịch', async () => {
  const res = await t.post('/api/campaigns', { name: '', channel: 'tivi', budget: -5, start_date: '2026-12-01', end_date: '2026-11-01' });
  assert.equal(res.status, 422);
  assert.deepEqual(Object.keys(res.data.error.details).sort(), ['budget', 'channel', 'end_date', 'name']);
  await createCampaign();
  assert.equal((await t.post('/api/campaigns', CAMPAIGN)).status, 409);
});

test('AC80-03 sửa chiến dịch', async () => {
  const c = await createCampaign();
  assert.equal((await t.patch(`/api/campaigns/${c.id}`, { budget: 25000000 })).data.budget, 25000000);
  assert.equal((await t.patch(`/api/campaigns/${c.id}`, { end_date: '2025-01-01' })).status, 422);
});

test('AC80-04 chuyển đổi lead -> cơ hội kế thừa chiến dịch', async () => {
  const c = await createCampaign();
  const leadId = t.seedLead({ campaign_id: c.id, company: 'A Corp' });
  const res = await t.post(`/api/leads/${leadId}/convert`, { value: 50000000 });
  assert.equal(res.status, 201);
  assert.equal(res.data.opportunity.campaign_id, c.id);
  assert.equal(res.data.opportunity.lead_id, leadId);
  assert.equal(res.data.lead.status, 'Đã chuyển đổi');
  assert.equal((await t.post(`/api/leads/${leadId}/convert`, {})).status, 409);
});

test('AC80-05 không thể đổi chiến dịch gốc của lead / cơ hội', async () => {
  const c1 = await createCampaign();
  const c2 = await createCampaign({ name: 'Google Q4', channel: 'google_ads' });
  const leadId = t.seedLead({ campaign_id: c1.id });
  assert.equal((await t.patch(`/api/leads/${leadId}`, { campaign_id: c2.id })).status, 422);
  assert.equal((await t.post(`/api/leads/${leadId}/convert`, { campaign_id: c2.id })).status, 422);
  const opp = await convert(leadId);
  assert.equal((await t.patch(`/api/opportunities/${opp.id}`, { campaign_id: c2.id })).status, 422);
  assert.equal((await t.post('/api/opportunities', { name: 'X', lead_id: leadId, campaign_id: c2.id })).status, 422);
});

test('AC80-06 cơ hội Thắng phải có giá trị', async () => {
  const c = await createCampaign();
  const opp = (await t.post('/api/opportunities', { name: 'Deal', campaign_id: c.id })).data;
  assert.equal((await t.patch(`/api/opportunities/${opp.id}`, { stage: 'Thắng' })).status, 422);
  const ok = await t.patch(`/api/opportunities/${opp.id}`, { stage: 'Thắng', value: 1000000 });
  assert.equal(ok.status, 200);
  assert.equal(ok.data.is_closed, true);
  assert.ok(ok.data.closed_at);
});

async function seedTwoCampaigns() {
  const many = await createCampaign({ name: 'Nhiều lead', budget: 10000000 });
  const rich = await createCampaign({ name: 'Ra doanh thu', channel: 'hoi_thao', budget: 20000000 });
  const manyLeads = Array.from({ length: 10 }, (_, i) => t.seedLead({ full_name: `M${i}`, campaign_id: many.id }));
  const richLeads = Array.from({ length: 3 }, (_, i) => t.seedLead({ full_name: `R${i}`, campaign_id: rich.id }));
  let o = await convert(manyLeads[0]);
  await t.patch(`/api/opportunities/${o.id}`, { stage: 'Thắng', value: 5000000 });
  o = await convert(manyLeads[1]);
  await t.patch(`/api/opportunities/${o.id}`, { stage: 'Thua' });
  for (const [leadId, value] of [[richLeads[0], 60000000], [richLeads[1], 40000000]]) {
    o = await convert(leadId);
    await t.patch(`/api/opportunities/${o.id}`, { stage: 'Thắng', value });
  }
  await convert(richLeads[2], { value: 7000000 });
  return { many, rich };
}

test('AC80-07 báo cáo từng chiến dịch', async () => {
  const { many, rich } = await seedTwoCampaigns();
  const r = (await t.get(`/api/campaigns/${rich.id}/report`)).data;
  assert.deepEqual([r.lead_count, r.opportunity_count, r.won_count, r.won_value, r.pipeline_value], [3, 3, 2, 100000000, 7000000]);
  assert.equal(r.cost_per_lead, Math.round((20000000 / 3) * 100) / 100);
  assert.equal(r.roi_percent, 400);
  const m = (await t.get(`/api/campaigns/${many.id}/report`)).data;
  assert.deepEqual([m.lead_count, m.opportunity_count, m.won_value, m.win_rate, m.roi_percent], [10, 2, 5000000, 50, -50]);
});

test('AC80-08 xếp hạng theo doanh thu, không theo số lead', async () => {
  const { many, rich } = await seedTwoCampaigns();
  t.seedLead({ full_name: 'Không chiến dịch' });
  const rep = (await t.get('/api/reports/campaigns')).data;
  assert.deepEqual(rep.items.map((i) => i.campaign_id), [rich.id, many.id]);
  assert.equal(rep.top_by_revenue, rich.id);
  assert.equal(rep.top_by_leads, many.id);
  assert.ok(rep.insight);
  assert.equal(rep.totals.won_value, 105000000);
  assert.equal(rep.unassigned.lead_count, 1);
  const byLeads = (await t.get('/api/reports/campaigns?sort=lead_count')).data;
  assert.equal(byLeads.items[0].campaign_id, many.id);
});

test('AC80-09 danh sách lead của chiến dịch', async () => {
  const c = await createCampaign();
  t.seedLead({ campaign_id: c.id });
  t.seedLead();
  assert.equal((await t.get(`/api/campaigns/${c.id}/leads`)).data.total, 1);
});
