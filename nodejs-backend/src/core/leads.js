'use strict';
/** Truy vấn lead dùng chung + API đọc/cập nhật lead (mọi feature đều dùng). */
const {
  LEAD_SOURCES, LEAD_STATUSES, LEAD_STATUS_NEW, LEAD_STATUS_CONVERTED,
  MANUAL_SOURCES, CAMPAIGN_CHANNELS, OPPORTUNITY_STAGES,
} = require('./constants');
const { ApiError, cleanText, nowIso, parseOptionalId } = require('./utils');

const leadToDto = (lead) => ({ ...lead, source_label: LEAD_SOURCES[lead.source] || lead.source });

function getLeadOr404(db, id) {
  const lead = db.get('leads', id);
  if (!lead) throw new ApiError(404, `Không tìm thấy lead #${id}`);
  return lead;
}

/** Trả về { id, error } */
function resolveCampaignId(db, value) {
  if (value === null || value === undefined || value === '') return { id: null, error: null };
  const id = Number(value);
  if (!Number.isInteger(id) || id <= 0) return { id: null, error: 'Mã chiến dịch không hợp lệ' };
  if (!db.get('campaigns', id)) return { id: null, error: `Chiến dịch #${id} không tồn tại` };
  return { id, error: null };
}

function findDuplicateLead(db, email, phone) {
  if (!email && !phone) return null;
  return db.findOne('leads', (l) => (email && l.email === email) || (phone && l.phone === phone));
}

/** Hàm DUY NHẤT để tạo lead — đảm bảo mọi lead đều có nguồn hợp lệ. */
function insertLead(db, data) {
  const source = cleanText(data.source);
  if (!LEAD_SOURCES[source]) {
    throw new ApiError(422, 'Lead bắt buộc phải có nguồn hợp lệ', { source: 'Thiếu hoặc sai nguồn lead' });
  }
  if (!cleanText(data.full_name)) {
    throw new ApiError(422, 'Lead bắt buộc phải có họ tên', { full_name: 'Họ tên là bắt buộc' });
  }
  const ts = nowIso();
  return db.insert('leads', {
    full_name: cleanText(data.full_name),
    email: data.email || null,
    phone: data.phone || null,
    company: data.company || null,
    interest: data.interest || null,
    note: data.note || null,
    status: data.status || LEAD_STATUS_NEW,
    source,
    source_detail: data.source_detail || null,
    form_id: data.form_id || null,
    campaign_id: data.campaign_id || null,
    import_batch_id: data.import_batch_id || null,
    ip_address: data.ip_address || null,
    created_by: data.created_by || null,
    created_at: ts,
    updated_at: ts,
  });
}

function registerCoreRoutes(router) {
  router.get('/api/meta', () => ({
    json: {
      lead_statuses: LEAD_STATUSES,
      lead_sources: Object.entries(LEAD_SOURCES).map(([code, label]) => ({ code, label })),
      manual_sources: MANUAL_SOURCES.map((code) => ({ code, label: LEAD_SOURCES[code] })),
      campaign_channels: Object.entries(CAMPAIGN_CHANNELS).map(([code, label]) => ({ code, label })),
      opportunity_stages: OPPORTUNITY_STAGES,
    },
  }));

  router.get('/api/leads', ({ db, query }) => {
    const filters = [];
    for (const f of ['status', 'source']) {
      if (query.get(f)) filters.push((l) => l[f] === query.get(f));
    }
    for (const f of ['campaign_id', 'form_id', 'import_batch_id']) {
      const v = query.get(f);
      if (v === 'none') filters.push((l) => l[f] === null);
      else if (v) {
        const id = parseOptionalId(v, f);
        filters.push((l) => l[f] === id);
      }
    }
    const q = cleanText(query.get('q')).toLowerCase();
    if (q) {
      filters.push((l) => [l.full_name, l.email, l.phone, l.company]
        .some((x) => (x || '').toLowerCase().includes(q)));
    }
    const page = Math.max(parseInt(query.get('page') || '1', 10) || 1, 1);
    const pageSize = Math.min(Math.max(parseInt(query.get('page_size') || '20', 10) || 20, 1), 200);
    const all = db.filter('leads', (l) => filters.every((fn) => fn(l))).sort((a, b) => b.id - a.id);
    return {
      json: {
        items: all.slice((page - 1) * pageSize, page * pageSize).map(leadToDto),
        total: all.length,
        page,
        page_size: pageSize,
      },
    };
  });

  router.get('/api/leads/:id', ({ db, params }) => {
    const id = parseOptionalId(params.id, 'id');
    return { json: leadToDto(getLeadOr404(db, id)) };
  });

  router.patch('/api/leads/:id', ({ db, params, body }) => {
    const id = parseOptionalId(params.id, 'id');
    getLeadOr404(db, id);
    const locked = ['source', 'campaign_id', 'form_id', 'import_batch_id'].filter((k) => k in body);
    if (locked.length) {
      throw new ApiError(422, 'Không được thay đổi nguồn và chiến dịch gốc đã sinh ra lead',
        Object.fromEntries(locked.map((k) => [k, 'Trường này không được phép sửa'])));
    }
    const updates = {};
    const errors = {};
    if ('status' in body) {
      const status = cleanText(body.status);
      if (status === LEAD_STATUS_CONVERTED) errors.status = 'Hãy dùng chức năng chuyển đổi lead để tạo cơ hội';
      else if (!LEAD_STATUSES.includes(status)) errors.status = `Trạng thái phải là một trong: ${LEAD_STATUSES.join(', ')}`;
      else updates.status = status;
    }
    for (const [field, limit] of [['company', 200], ['interest', 2000], ['note', 2000]]) {
      if (field in body) {
        const value = cleanText(body[field], true);
        if (value.length > limit) errors[field] = `Tối đa ${limit} ký tự`;
        else updates[field] = value || null;
      }
    }
    if (Object.keys(errors).length) throw new ApiError(422, 'Dữ liệu chưa hợp lệ', errors);
    if (Object.keys(updates).length) db.update('leads', id, { ...updates, updated_at: nowIso() });
    return { json: leadToDto(getLeadOr404(db, id)) };
  });
}

module.exports = {
  leadToDto, getLeadOr404, resolveCampaignId, findDuplicateLead, insertLead, registerCoreRoutes,
};
