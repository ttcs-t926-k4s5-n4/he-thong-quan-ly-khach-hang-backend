'use strict';
/**
 * SCRUM-80 — Là Nhân viên Marketing, tôi muốn theo dõi lead theo từng chiến dịch, để đo được
 * chiến dịch nào thực sự ra doanh thu chứ không chỉ ra nhiều lead.
 *
 * Chức năng:
 *  - Khai báo chiến dịch: tên, kênh, ngân sách, thời gian chạy (bắt đầu - kết thúc).
 *  - Lead và cơ hội giữ liên kết cố định tới chiến dịch đã sinh ra chúng
 *    (chuyển đổi lead -> cơ hội kế thừa chiến dịch, không cho sửa chiến dịch gốc).
 *  - Báo cáo từng chiến dịch: số lead, số cơ hội, giá trị đã chốt, tỷ lệ chuyển đổi, chi phí/lead, ROI.
 *  - Báo cáo tổng hợp xếp hạng chiến dịch theo doanh thu (không chỉ theo số lead).
 */
const {
  CAMPAIGN_CHANNELS, LEAD_SOURCES, LEAD_STATUS_CONVERTED, LEAD_STATUS_DISQUALIFIED,
  OPEN_STAGES, OPPORTUNITY_STAGES, STAGE_WON, STAGE_LOST,
} = require('../core/constants');
const {
  ApiError, cleanText, nowIso, isValidDate, parseMoney, parseOptionalId, pct, round2,
} = require('../core/utils');
const { getLeadOr404, leadToDto, resolveCampaignId } = require('../core/leads');

const FEATURE = {
  key: 'SCRUM-80',
  branch: 'feature/SCRUM-80-campaign-tracking-backend',
  name: 'Theo dõi lead theo chiến dịch và đo doanh thu',
};

const CAMPAIGN_FIELDS = ['name', 'channel', 'budget', 'start_date', 'end_date', 'description'];
const SORT_KEYS = ['won_value', 'roi_percent', 'lead_count', 'opportunity_count', 'win_rate'];

// ------------------------------------------------------------------ helpers
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

function campaignStatus(c) {
  const t = today();
  if (t < c.start_date) return 'Sắp chạy';
  if (t > c.end_date) return 'Đã kết thúc';
  return 'Đang chạy';
}

const campaignToDto = (c) => ({ ...c, channel_label: CAMPAIGN_CHANNELS[c.channel] || c.channel, status: campaignStatus(c) });

function getCampaignOr404(db, id) {
  const c = db.get('campaigns', id);
  if (!c) throw new ApiError(404, `Không tìm thấy chiến dịch #${id}`);
  return c;
}

function validateCampaign(data, existing = null) {
  const merged = { ...(existing || {}) };
  CAMPAIGN_FIELDS.forEach((k) => { if (k in data) merged[k] = data[k]; });
  const values = {};
  const errors = {};

  const name = cleanText(merged.name);
  if (!name) errors.name = 'Tên chiến dịch là bắt buộc';
  else if (name.length > 150) errors.name = 'Tên chiến dịch tối đa 150 ký tự';
  values.name = name;

  const channel = cleanText(merged.channel).toLowerCase();
  if (!CAMPAIGN_CHANNELS[channel]) errors.channel = `Kênh phải là một trong: ${Object.keys(CAMPAIGN_CHANNELS).join(', ')}`;
  values.channel = channel;

  const budget = parseMoney(merged.budget);
  if (budget === null) errors.budget = 'Ngân sách là bắt buộc và phải là số >= 0';
  values.budget = budget;

  for (const [field, label] of [['start_date', 'Ngày bắt đầu'], ['end_date', 'Ngày kết thúc']]) {
    const v = cleanText(merged[field]);
    if (!isValidDate(v)) errors[field] = `${label} phải có dạng YYYY-MM-DD`;
    values[field] = v;
  }
  if (!errors.start_date && !errors.end_date && values.end_date < values.start_date) {
    errors.end_date = 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu';
  }
  const description = cleanText(merged.description, true);
  if (description.length > 2000) errors.description = 'Mô tả tối đa 2000 ký tự';
  values.description = description || null;
  return { values, errors };
}

function campaignMetrics(db, c) {
  const leads = db.filter('leads', (l) => l.campaign_id === c.id);
  const opps = db.filter('opportunities', (o) => o.campaign_id === c.id);
  const won = opps.filter((o) => o.stage === STAGE_WON);
  const lost = opps.filter((o) => o.stage === STAGE_LOST);
  const wonValue = round2(won.reduce((s, o) => s + o.value, 0));
  const pipeline = round2(opps.filter((o) => OPEN_STAGES.includes(o.stage)).reduce((s, o) => s + o.value, 0));
  const bySource = {};
  leads.forEach((l) => { bySource[l.source] = (bySource[l.source] || 0) + 1; });
  const budget = Number(c.budget);
  return {
    campaign_id: c.id,
    campaign_name: c.name,
    channel: c.channel,
    channel_label: CAMPAIGN_CHANNELS[c.channel] || c.channel,
    status: campaignStatus(c),
    start_date: c.start_date,
    end_date: c.end_date,
    budget,
    lead_count: leads.length,
    converted_lead_count: leads.filter((l) => l.status === LEAD_STATUS_CONVERTED).length,
    opportunity_count: opps.length,
    open_opportunity_count: opps.length - won.length - lost.length,
    won_count: won.length,
    lost_count: lost.length,
    won_value: wonValue,
    pipeline_value: pipeline,
    lead_to_opportunity_rate: pct(opps.length, leads.length),
    win_rate: pct(won.length, won.length + lost.length),
    cost_per_lead: leads.length ? round2(budget / leads.length) : null,
    cost_per_won_deal: won.length ? round2(budget / won.length) : null,
    roi_percent: budget ? round2(((wonValue - budget) * 100) / budget) : null,
    leads_by_source: Object.entries(bySource)
      .sort((a, b) => b[1] - a[1])
      .map(([source, count]) => ({ source, source_label: LEAD_SOURCES[source] || source, count })),
  };
}

const oppToDto = (o) => ({ ...o, is_closed: [STAGE_WON, STAGE_LOST].includes(o.stage) });

function getOppOr404(db, id) {
  const o = db.get('opportunities', id);
  if (!o) throw new ApiError(404, `Không tìm thấy cơ hội #${id}`);
  return o;
}

function validateStageValue(stage, value, errors) {
  if (!OPPORTUNITY_STAGES.includes(stage)) errors.stage = `Giai đoạn phải là một trong: ${OPPORTUNITY_STAGES.join(', ')}`;
  if (value === null) errors.value = 'Giá trị phải là số >= 0';
  else if (stage === STAGE_WON && value <= 0) errors.value = 'Cơ hội đã Thắng phải có giá trị chốt > 0';
}

function validateCloseDate(value, errors) {
  const v = cleanText(value);
  if (v && !isValidDate(v)) errors.expected_close_date = 'Ngày dự kiến chốt phải có dạng YYYY-MM-DD';
  return v || null;
}

const hasErrors = (e) => Object.keys(e).length > 0;

// ------------------------------------------------------------------ routes
function register(router) {
  // ---- Chiến dịch ----
  router.post('/api/campaigns', ({ db, body, userId }) => {
    const { values, errors } = validateCampaign(body);
    if (!hasErrors(errors) && db.findOne('campaigns', (c) => c.name === values.name)) {
      throw new ApiError(409, `Chiến dịch '${values.name}' đã tồn tại`);
    }
    if (hasErrors(errors)) throw new ApiError(422, 'Dữ liệu chiến dịch chưa hợp lệ', errors);
    const ts = nowIso();
    const c = db.insert('campaigns', { ...values, created_by: userId, created_at: ts, updated_at: ts });
    return { status: 201, json: campaignToDto(c) };
  });

  router.get('/api/campaigns', ({ db, query }) => {
    const channel = query.get('channel');
    const q = cleanText(query.get('q')).toLowerCase();
    const status = query.get('status');
    const items = db.filter('campaigns', (c) => (!channel || c.channel === channel)
      && (!q || c.name.toLowerCase().includes(q)))
      .map(campaignToDto)
      .filter((c) => !status || c.status === status)
      .sort((a, b) => (b.start_date.localeCompare(a.start_date)) || b.id - a.id);
    return { json: { items, total: items.length } };
  });

  router.get('/api/campaigns/:id', ({ db, params }) => {
    const c = getCampaignOr404(db, parseOptionalId(params.id, 'id'));
    return { json: { ...campaignToDto(c), summary: campaignMetrics(db, c) } };
  });

  router.patch('/api/campaigns/:id', ({ db, params, body }) => {
    const id = parseOptionalId(params.id, 'id');
    const existing = getCampaignOr404(db, id);
    const { values, errors } = validateCampaign(body, existing);
    if (!hasErrors(errors) && db.findOne('campaigns', (c) => c.name === values.name && c.id !== id)) {
      throw new ApiError(409, `Chiến dịch '${values.name}' đã tồn tại`);
    }
    if (hasErrors(errors)) throw new ApiError(422, 'Dữ liệu chiến dịch chưa hợp lệ', errors);
    return { json: campaignToDto(db.update('campaigns', id, { ...values, updated_at: nowIso() })) };
  });

  router.get('/api/campaigns/:id/leads', ({ db, params }) => {
    const id = parseOptionalId(params.id, 'id');
    getCampaignOr404(db, id);
    const items = db.filter('leads', (l) => l.campaign_id === id).sort((a, b) => b.id - a.id).map(leadToDto);
    return { json: { items, total: items.length } };
  });

  router.get('/api/campaigns/:id/report', ({ db, params }) => {
    const c = getCampaignOr404(db, parseOptionalId(params.id, 'id'));
    return { json: campaignMetrics(db, c) };
  });

  router.get('/api/reports/campaigns', ({ db, query }) => {
    const sort = query.get('sort') || 'won_value';
    if (!SORT_KEYS.includes(sort)) throw new ApiError(400, `sort phải là ${SORT_KEYS.join(' | ')}`);
    const channel = query.get('channel');
    const from = query.get('from');
    const to = query.get('to');
    if ((from && !isValidDate(from)) || (to && !isValidDate(to))) throw new ApiError(400, 'from/to phải có dạng YYYY-MM-DD');

    const items = db.filter('campaigns', (c) => (!channel || c.channel === channel)
      && (!from || c.end_date >= from) && (!to || c.start_date <= to))
      .map((c) => campaignMetrics(db, c));
    const val = (m) => (m[sort] === null ? -Infinity : m[sort]);
    items.sort((a, b) => (val(b) - val(a)) || (b.won_value - a.won_value));
    items.forEach((m, i) => { m.rank = i + 1; });

    const totalBudget = items.reduce((s, i) => s + i.budget, 0);
    const totalWon = items.reduce((s, i) => s + i.won_value, 0);
    const topRevenue = items.reduce((best, m) => (!best || m.won_value > best.won_value ? m : best), null);
    const topLeads = items.reduce((best, m) => (!best || m.lead_count > best.lead_count ? m : best), null);
    let insight = null;
    if (topRevenue && topLeads && topRevenue.won_value > 0 && topRevenue.campaign_id !== topLeads.campaign_id) {
      insight = `'${topLeads.campaign_name}' ra nhiều lead nhất (${topLeads.lead_count}) nhưng `
        + `'${topRevenue.campaign_name}' mới là chiến dịch ra doanh thu cao nhất `
        + `(${topRevenue.won_value.toLocaleString('en-US')}).`;
    }
    const unassignedWon = db.filter('opportunities', (o) => o.campaign_id === null && o.stage === STAGE_WON)
      .reduce((s, o) => s + o.value, 0);
    return {
      json: {
        sort,
        items,
        totals: {
          campaign_count: items.length,
          budget: round2(totalBudget),
          lead_count: items.reduce((s, i) => s + i.lead_count, 0),
          opportunity_count: items.reduce((s, i) => s + i.opportunity_count, 0),
          won_value: round2(totalWon),
          roi_percent: totalBudget ? round2(((totalWon - totalBudget) * 100) / totalBudget) : null,
        },
        top_by_revenue: topRevenue && topRevenue.won_value > 0 ? topRevenue.campaign_id : null,
        top_by_leads: topLeads && topLeads.lead_count > 0 ? topLeads.campaign_id : null,
        insight,
        unassigned: {
          lead_count: db.count('leads', (l) => l.campaign_id === null),
          won_value: round2(unassignedWon),
        },
      },
    };
  });

  // ---- Chuyển đổi lead -> cơ hội ----
  router.post('/api/leads/:id/convert', ({ db, params, body, userId }) => {
    const leadId = parseOptionalId(params.id, 'id');
    const lead = getLeadOr404(db, leadId);
    if (lead.status === LEAD_STATUS_CONVERTED) throw new ApiError(409, 'Lead này đã được chuyển đổi thành cơ hội');
    if (lead.status === LEAD_STATUS_DISQUALIFIED) throw new ApiError(409, "Lead ở trạng thái 'Không đạt' không thể chuyển đổi");
    if ('campaign_id' in body) {
      throw new ApiError(422, 'Cơ hội tự kế thừa chiến dịch của lead, không được chỉ định chiến dịch khác',
        { campaign_id: 'Không được phép gửi trường này' });
    }
    const errors = {};
    const name = cleanText(body.name) || `Cơ hội - ${lead.company || lead.full_name}`;
    if (name.length > 200) errors.name = 'Tên cơ hội tối đa 200 ký tự';
    const value = parseMoney(body.value === undefined ? 0 : body.value);
    const stage = cleanText(body.stage) || OPPORTUNITY_STAGES[0];
    validateStageValue(stage, value, errors);
    const closeDate = validateCloseDate(body.expected_close_date, errors);
    if (hasErrors(errors)) throw new ApiError(422, 'Dữ liệu cơ hội chưa hợp lệ', errors);

    const ts = nowIso();
    const opp = db.transaction(() => {
      const o = db.insert('opportunities', {
        name,
        lead_id: leadId,
        campaign_id: lead.campaign_id,
        stage,
        value,
        expected_close_date: closeDate,
        closed_at: [STAGE_WON, STAGE_LOST].includes(stage) ? ts : null,
        created_by: userId,
        created_at: ts,
        updated_at: ts,
      });
      db.update('leads', leadId, { status: LEAD_STATUS_CONVERTED, updated_at: ts });
      return o;
    });
    return {
      status: 201,
      json: {
        message: 'Đã chuyển đổi lead thành cơ hội',
        opportunity: oppToDto(opp),
        lead: leadToDto(getLeadOr404(db, leadId)),
      },
    };
  });

  // ---- Cơ hội ----
  router.post('/api/opportunities', ({ db, body, userId }) => {
    const errors = {};
    const name = cleanText(body.name);
    if (!name) errors.name = 'Tên cơ hội là bắt buộc';
    const leadId = parseOptionalId(body.lead_id, 'lead_id');
    const campaign = resolveCampaignId(db, body.campaign_id);
    if (campaign.error) errors.campaign_id = campaign.error;
    let campaignId = campaign.id;
    if (leadId) {
      const lead = getLeadOr404(db, leadId);
      if (body.campaign_id !== undefined && body.campaign_id !== null && body.campaign_id !== ''
        && campaignId !== lead.campaign_id) {
        errors.campaign_id = 'Chiến dịch của cơ hội phải trùng với chiến dịch đã sinh ra lead';
      }
      campaignId = lead.campaign_id;
    }
    const value = parseMoney(body.value === undefined ? 0 : body.value);
    const stage = cleanText(body.stage) || OPPORTUNITY_STAGES[0];
    validateStageValue(stage, value, errors);
    const closeDate = validateCloseDate(body.expected_close_date, errors);
    if (hasErrors(errors)) throw new ApiError(422, 'Dữ liệu cơ hội chưa hợp lệ', errors);
    const ts = nowIso();
    const opp = db.insert('opportunities', {
      name,
      lead_id: leadId,
      campaign_id: campaignId,
      stage,
      value,
      expected_close_date: closeDate,
      closed_at: [STAGE_WON, STAGE_LOST].includes(stage) ? ts : null,
      created_by: userId,
      created_at: ts,
      updated_at: ts,
    });
    return { status: 201, json: oppToDto(opp) };
  });

  router.get('/api/opportunities', ({ db, query }) => {
    const campaignId = query.get('campaign_id') ? parseOptionalId(query.get('campaign_id'), 'campaign_id') : null;
    const leadId = query.get('lead_id') ? parseOptionalId(query.get('lead_id'), 'lead_id') : null;
    const stage = query.get('stage');
    const items = db.filter('opportunities', (o) => (!campaignId || o.campaign_id === campaignId)
      && (!leadId || o.lead_id === leadId) && (!stage || o.stage === stage))
      .sort((a, b) => b.id - a.id).map(oppToDto);
    return { json: { items, total: items.length } };
  });

  router.get('/api/opportunities/:id', ({ db, params }) => ({
    json: oppToDto(getOppOr404(db, parseOptionalId(params.id, 'id'))),
  }));

  router.patch('/api/opportunities/:id', ({ db, params, body }) => {
    const id = parseOptionalId(params.id, 'id');
    const current = getOppOr404(db, id);
    const locked = ['campaign_id', 'lead_id'].filter((k) => k in body);
    if (locked.length) {
      throw new ApiError(422, 'Không được thay đổi chiến dịch / lead gốc của cơ hội',
        Object.fromEntries(locked.map((k) => [k, 'Trường này không được phép sửa'])));
    }
    const errors = {};
    const name = 'name' in body ? cleanText(body.name) : current.name;
    if (!name) errors.name = 'Tên cơ hội là bắt buộc';
    const stage = 'stage' in body ? cleanText(body.stage) : current.stage;
    const value = 'value' in body ? parseMoney(body.value) : current.value;
    validateStageValue(stage, value, errors);
    const closeDate = 'expected_close_date' in body
      ? validateCloseDate(body.expected_close_date, errors) : current.expected_close_date;
    if (hasErrors(errors)) throw new ApiError(422, 'Dữ liệu cơ hội chưa hợp lệ', errors);
    const ts = nowIso();
    const closed = [STAGE_WON, STAGE_LOST].includes(stage);
    let closedAt = current.closed_at;
    if (closed && current.stage !== stage) closedAt = ts;
    else if (!closed) closedAt = null;
    const updated = db.update('opportunities', id, {
      name, stage, value, expected_close_date: closeDate, closed_at: closedAt, updated_at: ts,
    });
    return { json: oppToDto(updated) };
  });
}

module.exports = { FEATURE, register };
