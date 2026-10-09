'use strict';
/**
 * SCRUM-78 — Là Nhân viên Marketing, tôi muốn thu thập lead từ biểu mẫu nhúng trên website,
 * để mọi lead vào thẳng hệ thống thay vì nằm trong hộp thư chung.
 *
 * Chức năng:
 *  - Quản lý biểu mẫu (tạo / xem / sửa / bật-tắt) gắn với chiến dịch và danh sách domain được phép.
 *  - Sinh mã nhúng (script hoặc iframe) dán được vào website bất kỳ.
 *  - Endpoint công khai nhận: họ tên, email, SĐT, công ty, nhu cầu quan tâm.
 *  - Chống spam: honeypot, bẫy thời gian điền form, kiểm tra domain, giới hạn tần suất theo IP.
 *  - Gửi thành công -> tạo lead trạng thái "Mới", nguồn "web_form", gắn đúng biểu mẫu & chiến dịch.
 */
const crypto = require('crypto');
const { LEAD_STATUS_NEW } = require('../core/constants');
const {
  ApiError, cleanText, nowIso, normalizeEmail, isValidEmail, normalizePhone, isValidPhone, parseOptionalId,
} = require('../core/utils');
const { insertLead, resolveCampaignId } = require('../core/leads');
const { parseRate } = require('../core/rateLimiter');

const FEATURE = {
  key: 'SCRUM-78',
  branch: 'feature/SCRUM-78-lead-web-form-backend',
  name: 'Thu thập lead từ biểu mẫu nhúng trên website',
};

const DEFAULT_SUCCESS_MESSAGE = 'Cảm ơn bạn! Chúng tôi sẽ liên hệ lại trong thời gian sớm nhất.';
const HONEYPOT_FIELD = 'website_url';
const DOMAIN_RE = /^(localhost|([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63})$/;

const FORM_FIELDS = [
  { name: 'full_name', label: 'Họ và tên', type: 'text', required: true, max: 150 },
  { name: 'email', label: 'Email', type: 'email', required: true, max: 254 },
  { name: 'phone', label: 'Số điện thoại', type: 'tel', required: true, max: 20 },
  { name: 'company', label: 'Công ty', type: 'text', required: false, max: 200 },
  { name: 'interest', label: 'Nhu cầu quan tâm', type: 'textarea', required: false, max: 2000 },
];

const EMBED_JS_TEMPLATE = `(function () {
  var CFG = __CONFIG__;
  var host = document.getElementById(CFG.containerId);
  if (!host) {
    host = document.createElement("div");
    var s = document.currentScript;
    if (s && s.parentNode) { s.parentNode.insertBefore(host, s.nextSibling); } else { document.body.appendChild(host); }
  }
  if (host.getAttribute("data-crm-ready")) { return; }
  host.setAttribute("data-crm-ready", "1");
  var renderedAt = Date.now();
  var form = document.createElement("form");
  form.noValidate = true;
  form.style.cssText = "max-width:480px;display:grid;gap:12px;font-family:inherit";
  CFG.fields.forEach(function (f) {
    var wrap = document.createElement("label");
    wrap.style.cssText = "display:grid;gap:4px;font-size:14px";
    var title = document.createElement("span");
    title.textContent = f.label + (f.required ? " *" : "");
    var input = document.createElement(f.type === "textarea" ? "textarea" : "input");
    if (f.type !== "textarea") { input.type = f.type; }
    input.name = f.name;
    input.maxLength = f.max;
    if (f.required) { input.required = true; }
    input.style.cssText = "padding:8px 10px;border:1px solid #c8c8c8;border-radius:6px;font:inherit";
    var err = document.createElement("small");
    err.style.color = "#c0392b";
    err.setAttribute("data-error-for", f.name);
    wrap.appendChild(title); wrap.appendChild(input); wrap.appendChild(err);
    form.appendChild(wrap);
  });
  var hp = document.createElement("input");
  hp.type = "text"; hp.name = CFG.honeypot; hp.tabIndex = -1; hp.autocomplete = "off";
  hp.setAttribute("aria-hidden", "true");
  hp.style.cssText = "position:absolute;left:-9999px;width:1px;height:1px;opacity:0";
  form.appendChild(hp);
  var btn = document.createElement("button");
  btn.type = "submit"; btn.textContent = "Gửi thông tin";
  btn.style.cssText = "padding:10px 14px;border:0;border-radius:6px;background:#1f6feb;color:#fff;font:inherit;cursor:pointer";
  var msg = document.createElement("div");
  msg.setAttribute("role", "status");
  form.appendChild(btn); form.appendChild(msg);
  host.appendChild(form);
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var payload = { _ts: renderedAt };
    Array.prototype.forEach.call(form.elements, function (el) { if (el.name) { payload[el.name] = el.value; } });
    Array.prototype.forEach.call(form.querySelectorAll("[data-error-for]"), function (el) { el.textContent = ""; });
    msg.textContent = ""; btn.disabled = true; btn.textContent = "Đang gửi...";
    fetch(CFG.submitUrl, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (res.ok) {
          if (res.data.redirect_url) {
            try { window.top.location.href = res.data.redirect_url; } catch (x) { window.location.href = res.data.redirect_url; }
            return;
          }
          form.reset(); renderedAt = Date.now();
          msg.style.color = "#1e8449"; msg.textContent = res.data.message || CFG.successMessage;
          return;
        }
        var er = (res.data && res.data.error) || {};
        var details = er.details || {};
        Object.keys(details).forEach(function (k) {
          var el = form.querySelector('[data-error-for="' + k + '"]');
          if (el) { el.textContent = details[k]; }
        });
        msg.style.color = "#c0392b"; msg.textContent = er.message || "Không gửi được, vui lòng thử lại.";
      })
      .catch(function () { msg.style.color = "#c0392b"; msg.textContent = "Lỗi kết nối, vui lòng thử lại."; })
      .then(function () { btn.disabled = false; btn.textContent = "Gửi thông tin"; });
  });
})();
`;

// ------------------------------------------------------------------ helpers
const hostOf = (value) => {
  try { return new URL(value).hostname.toLowerCase(); } catch (e) { return ''; }
};
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function buildEmbed(form, baseUrl) {
  const key = form.public_key;
  return {
    public_key: key,
    script: `<div id="crm-lead-form-${key}"></div>\n<script src="${baseUrl}/embed/${key}.js" async></script>`,
    iframe: `<iframe src="${baseUrl}/embed/${key}/page" width="100%" height="640" style="border:0" title="Biểu mẫu liên hệ" loading="lazy"></iframe>`,
    submit_url: `${baseUrl}/public/forms/${key}/submit`,
  };
}

const formToDto = (form, baseUrl, withEmbed = false) => {
  const dto = { ...form, is_active: Boolean(form.is_active) };
  if (withEmbed) dto.embed = buildEmbed(form, baseUrl);
  return dto;
};

function getFormOr404(db, id) {
  const form = db.get('web_forms', id);
  if (!form) throw new ApiError(404, `Không tìm thấy biểu mẫu #${id}`);
  return form;
}

function normalizeDomains(value) {
  if (value === null || value === undefined || value === '') return { domains: [] };
  const items = typeof value === 'string' ? value.split(',') : value;
  if (!Array.isArray(items)) return { error: 'allowed_domains phải là danh sách tên miền' };
  const domains = [];
  for (const item of items) {
    let text = cleanText(item).toLowerCase();
    if (!text) continue;
    if (text.includes('://')) text = hostOf(text);
    text = text.split('/')[0].split(':')[0];
    if (text.startsWith('*.')) text = text.slice(2);
    if (!DOMAIN_RE.test(text)) return { error: `Tên miền không hợp lệ: ${item}` };
    if (!domains.includes(text)) domains.push(text);
  }
  return { domains };
}

function validateFormPayload(db, data, partial = false) {
  const values = {};
  const errors = {};
  const has = (k) => k in data || !partial;
  if (has('name')) {
    const name = cleanText(data.name);
    if (!name) errors.name = 'Tên biểu mẫu là bắt buộc';
    else if (name.length > 150) errors.name = 'Tên biểu mẫu tối đa 150 ký tự';
    values.name = name;
  }
  if (has('allowed_domains')) {
    const { domains, error } = normalizeDomains(data.allowed_domains);
    if (error) errors.allowed_domains = error;
    else values.allowed_domains = domains;
  }
  if (has('success_message')) {
    const msg = cleanText(data.success_message) || DEFAULT_SUCCESS_MESSAGE;
    if (msg.length > 300) errors.success_message = 'Thông báo tối đa 300 ký tự';
    values.success_message = msg;
  }
  if (has('redirect_url')) {
    const url = cleanText(data.redirect_url);
    if (url && !/^https?:\/\//i.test(url)) errors.redirect_url = 'redirect_url phải bắt đầu bằng http:// hoặc https://';
    values.redirect_url = url || null;
  }
  if (has('campaign_id')) {
    const { id, error } = resolveCampaignId(db, data.campaign_id);
    if (error) errors.campaign_id = error;
    values.campaign_id = id;
  }
  if ('is_active' in data) {
    if (typeof data.is_active !== 'boolean') errors.is_active = 'is_active phải là true hoặc false';
    else values.is_active = data.is_active;
  }
  return { values, errors };
}

function checkOrigin(form, ctx) {
  const domains = form.allowed_domains || [];
  if (!domains.length) return;
  const host = hostOf(ctx.headers.origin || ctx.headers.referer || '');
  if (host && (host === ctx.hostName || domains.some((d) => host === d || host.endsWith(`.${d}`)))) return;
  throw new ApiError(403, 'Website này không được phép gửi dữ liệu vào biểu mẫu');
}

function detectSpam(data, config) {
  if (cleanText(data[HONEYPOT_FIELD])) return 'honeypot';
  const ts = data._ts;
  if (ts !== undefined && ts !== null && ts !== '') {
    const elapsed = Date.now() - Number(ts);
    if (!Number.isFinite(elapsed)) return 'invalid_ts';
    if (elapsed < config.MIN_FILL_SECONDS * 1000) return 'too_fast';
  }
  return null;
}

function validateSubmission(data) {
  const errors = {};
  const fullName = cleanText(data.full_name);
  if (!fullName) errors.full_name = 'Vui lòng nhập họ và tên';
  else if (fullName.length > 150) errors.full_name = 'Họ tên tối đa 150 ký tự';
  const email = normalizeEmail(data.email);
  if (!email) errors.email = 'Vui lòng nhập email';
  else if (!isValidEmail(email)) errors.email = 'Email không hợp lệ';
  const phoneRaw = cleanText(data.phone);
  const phone = normalizePhone(phoneRaw);
  if (!phoneRaw) errors.phone = 'Vui lòng nhập số điện thoại';
  else if (!isValidPhone(phone)) errors.phone = 'Số điện thoại không hợp lệ (VD: 0912345678)';
  const company = cleanText(data.company);
  if (company.length > 200) errors.company = 'Tên công ty tối đa 200 ký tự';
  const interest = cleanText(data.interest, true);
  if (interest.length > 2000) errors.interest = 'Nhu cầu quan tâm tối đa 2000 ký tự';
  return { values: { full_name: fullName, email, phone, company, interest }, errors };
}

const activeFormByKey = (db, key) => {
  const form = db.findOne('web_forms', (f) => f.public_key === key);
  return form && form.is_active ? form : null;
};

// ------------------------------------------------------------------ routes
function register(router) {
  // ---- API quản trị biểu mẫu ----
  router.post('/api/forms', ({ db, body, userId, baseUrl }) => {
    const { values, errors } = validateFormPayload(db, body);
    if (Object.keys(errors).length) throw new ApiError(422, 'Dữ liệu biểu mẫu chưa hợp lệ', errors);
    const ts = nowIso();
    const form = db.insert('web_forms', {
      ...values,
      public_key: crypto.randomBytes(16).toString('base64url'),
      is_active: true,
      created_by: userId,
      created_at: ts,
      updated_at: ts,
    });
    return { status: 201, json: formToDto(form, baseUrl, true) };
  });

  router.get('/api/forms', ({ db, baseUrl }) => {
    const items = db.filter('web_forms').sort((a, b) => b.id - a.id).map((f) => ({
      ...formToDto(f, baseUrl),
      lead_count: db.count('leads', (l) => l.form_id === f.id),
    }));
    return { json: { items, total: items.length } };
  });

  router.get('/api/forms/:id', ({ db, params, baseUrl }) => {
    const form = getFormOr404(db, parseOptionalId(params.id, 'id'));
    return { json: { ...formToDto(form, baseUrl, true), lead_count: db.count('leads', (l) => l.form_id === form.id) } };
  });

  router.patch('/api/forms/:id', ({ db, params, body, baseUrl }) => {
    const id = parseOptionalId(params.id, 'id');
    getFormOr404(db, id);
    const { values, errors } = validateFormPayload(db, body, true);
    if (Object.keys(errors).length) throw new ApiError(422, 'Dữ liệu biểu mẫu chưa hợp lệ', errors);
    if (Object.keys(values).length) db.update('web_forms', id, { ...values, updated_at: nowIso() });
    return { json: formToDto(getFormOr404(db, id), baseUrl, true) };
  });

  router.get('/api/forms/:id/embed-code', ({ db, params, baseUrl }) => {
    const form = getFormOr404(db, parseOptionalId(params.id, 'id'));
    return { json: buildEmbed(form, baseUrl) };
  });

  // ---- Endpoint công khai ----
  router.get('/embed/:key.js', ({ db, params, baseUrl }) => {
    const form = activeFormByKey(db, params.key);
    if (!form) {
      return {
        status: 404,
        contentType: 'application/javascript; charset=utf-8',
        body: 'console.warn("[CRM] Biểu mẫu không tồn tại hoặc đã ngừng hoạt động");',
      };
    }
    const cfg = {
      containerId: `crm-lead-form-${params.key}`,
      submitUrl: `${baseUrl}/public/forms/${params.key}/submit`,
      successMessage: form.success_message,
      honeypot: HONEYPOT_FIELD,
      fields: FORM_FIELDS,
    };
    const safe = JSON.stringify(cfg).replace(/<\//g, '<\\/');
    return {
      contentType: 'application/javascript; charset=utf-8',
      headers: { 'Cache-Control': 'public, max-age=300' },
      body: EMBED_JS_TEMPLATE.replace('__CONFIG__', () => safe),
    };
  });

  router.get('/embed/:key/page', ({ db, params }) => {
    const form = activeFormByKey(db, params.key);
    if (!form) {
      return { status: 404, contentType: 'text/html; charset=utf-8', body: '<p>Biểu mẫu không tồn tại hoặc đã ngừng hoạt động.</p>' };
    }
    const key = escapeHtml(params.key);
    return {
      contentType: 'text/html; charset=utf-8',
      body: `<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(form.name)}</title>
<style>body{margin:0;padding:16px;font-family:system-ui,Segoe UI,Arial,sans-serif}</style></head>
<body><div id="crm-lead-form-${key}"></div><script src="/embed/${key}.js"></script></body></html>`,
    };
  });

  router.post('/public/forms/:key/submit', (ctx) => {
    const { db, params, body, config, limiter, ip } = ctx;
    const form = activeFormByKey(db, params.key);
    if (!form) throw new ApiError(404, 'Biểu mẫu không tồn tại hoặc đã ngừng nhận dữ liệu');
    checkOrigin(form, ctx);

    const perForm = parseRate(config.RATE_LIMIT_PER_FORM);
    const perIp = parseRate(config.RATE_LIMIT_PER_IP);
    let r = limiter.hit(`form:${form.id}:${ip}`, perForm.limit, perForm.windowSeconds);
    if (r.allowed) r = limiter.hit(`ip:${ip}`, perIp.limit, perIp.windowSeconds);
    if (!r.allowed) {
      throw new ApiError(429, `Bạn gửi quá nhiều lần. Vui lòng thử lại sau ${r.retryAfter} giây.`, null,
        { 'Retry-After': String(r.retryAfter) });
    }

    const success = { message: form.success_message, redirect_url: form.redirect_url };
    const spam = detectSpam(body, config);
    if (spam) {
      // Trả về như thành công để bot không biết đã bị chặn, nhưng KHÔNG tạo lead
      console.warn(`Chặn spam biểu mẫu #${form.id} từ IP ${ip} (${spam})`);
      return { status: 201, json: success };
    }
    const { values, errors } = validateSubmission(body);
    if (Object.keys(errors).length) throw new ApiError(422, 'Dữ liệu chưa hợp lệ, vui lòng kiểm tra lại', errors);

    insertLead(db, {
      ...values,
      status: LEAD_STATUS_NEW,
      source: 'web_form',
      source_detail: form.name,
      form_id: form.id,
      campaign_id: form.campaign_id,
      ip_address: ip,
    });
    return { status: 201, json: success };
  });
}

module.exports = { FEATURE, register };
