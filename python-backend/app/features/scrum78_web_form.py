"""
SCRUM-78 — Là Nhân viên Marketing, tôi muốn thu thập lead từ biểu mẫu nhúng trên website,
để mọi lead vào thẳng hệ thống thay vì nằm trong hộp thư chung.

Chức năng:
  * Quản lý biểu mẫu (tạo / xem / sửa / bật-tắt) gắn với chiến dịch và danh sách domain được phép.
  * Sinh mã nhúng (script hoặc iframe) dán được vào website bất kỳ.
  * Endpoint công khai nhận dữ liệu: họ tên, email, SĐT, công ty, nhu cầu quan tâm.
  * Chống spam: honeypot, bẫy thời gian điền form, kiểm tra domain, giới hạn tần suất theo IP.
  * Gửi thành công -> tạo lead trạng thái "Mới", nguồn "web_form", gắn đúng biểu mẫu & chiến dịch.
"""
import html
import json
import re
import secrets
import time
from urllib.parse import urlparse

from flask import Blueprint, Response, current_app, request

from app.core import (
    LEAD_STATUS_NEW,
    ApiError,
    clean_text,
    client_ip,
    current_user,
    dumps,
    get_db,
    get_json_body,
    insert_lead,
    is_valid_email,
    is_valid_phone,
    normalize_email,
    normalize_phone,
    now_iso,
    parse_rate,
    resolve_campaign_id,
)

FEATURE = {
    "key": "SCRUM-78",
    "branch": "feature/SCRUM-78-lead-web-form-backend",
    "name": "Thu thập lead từ biểu mẫu nhúng trên website",
}

bp = Blueprint("scrum78_web_form", __name__)

DEFAULT_SUCCESS_MESSAGE = "Cảm ơn bạn! Chúng tôi sẽ liên hệ lại trong thời gian sớm nhất."
HONEYPOT_FIELD = "website_url"
DOMAIN_RE = re.compile(r"^(localhost|([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63})$")

FORM_FIELDS = [
    {"name": "full_name", "label": "Họ và tên", "type": "text", "required": True, "max": 150},
    {"name": "email", "label": "Email", "type": "email", "required": True, "max": 254},
    {"name": "phone", "label": "Số điện thoại", "type": "tel", "required": True, "max": 20},
    {"name": "company", "label": "Công ty", "type": "text", "required": False, "max": 200},
    {"name": "interest", "label": "Nhu cầu quan tâm", "type": "textarea", "required": False, "max": 2000},
]

EMBED_JS_TEMPLATE = r"""(function () {
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
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def base_url():
    return current_app.config.get("PUBLIC_BASE_URL") or request.host_url.rstrip("/")


def build_embed(form):
    base, key = base_url(), form["public_key"]
    return {
        "public_key": key,
        "script": f'<div id="crm-lead-form-{key}"></div>\n<script src="{base}/embed/{key}.js" async></script>',
        "iframe": (
            f'<iframe src="{base}/embed/{key}/page" width="100%" height="640" '
            f'style="border:0" title="Biểu mẫu liên hệ" loading="lazy"></iframe>'
        ),
        "submit_url": f"{base}/public/forms/{key}/submit",
    }


def form_to_dict(row, with_embed=False):
    data = dict(row)
    data["allowed_domains"] = json.loads(data.get("allowed_domains") or "[]")
    data["is_active"] = bool(data["is_active"])
    if with_embed:
        data["embed"] = build_embed(data)
    return data


def get_form_or_404(db, form_id):
    row = db.execute("SELECT * FROM web_forms WHERE id = ?", (form_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"Không tìm thấy biểu mẫu #{form_id}")
    return row


def normalize_domains(value):
    if value is None or value == "":
        return [], None
    items = value.split(",") if isinstance(value, str) else value
    if not isinstance(items, list):
        return None, "allowed_domains phải là danh sách tên miền"
    result = []
    for item in items:
        text = clean_text(item).lower()
        if not text:
            continue
        if "://" in text:
            text = urlparse(text).hostname or ""
        text = text.split("/")[0].split(":")[0]
        if text.startswith("*."):
            text = text[2:]
        if not DOMAIN_RE.match(text):
            return None, f"Tên miền không hợp lệ: {item}"
        if text not in result:
            result.append(text)
    return result, None


def validate_form_payload(data, partial=False):
    values, errors = {}, {}
    if "name" in data or not partial:
        name = clean_text(data.get("name"))
        if not name:
            errors["name"] = "Tên biểu mẫu là bắt buộc"
        elif len(name) > 150:
            errors["name"] = "Tên biểu mẫu tối đa 150 ký tự"
        values["name"] = name
    if "allowed_domains" in data or not partial:
        domains, err = normalize_domains(data.get("allowed_domains"))
        if err:
            errors["allowed_domains"] = err
        else:
            values["allowed_domains"] = json.dumps(domains)
    if "success_message" in data or not partial:
        msg = clean_text(data.get("success_message")) or DEFAULT_SUCCESS_MESSAGE
        if len(msg) > 300:
            errors["success_message"] = "Thông báo tối đa 300 ký tự"
