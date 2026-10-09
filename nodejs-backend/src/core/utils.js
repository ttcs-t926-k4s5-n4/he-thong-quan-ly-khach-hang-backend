'use strict';
/** Tiện ích kiểm tra & chuẩn hoá dữ liệu dùng chung. */

class ApiError extends Error {
  constructor(status, message, details = null, headers = {}) {
    super(message);
    this.status = status;
    this.details = details;
    this.headers = headers;
  }
}

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/;
const PHONE_RE = /^0\d{9}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const nowIso = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

function cleanText(value, keepNewlines = false) {
  if (value === null || value === undefined) return '';
  let text = String(value).trim();
  text = keepNewlines ? text.replace(/[ \t]+/g, ' ') : text.replace(/\s+/g, ' ');
  return text;
}

const normalizeEmail = (v) => cleanText(v).toLowerCase();
const isValidEmail = (v) => Boolean(v) && v.length <= 254 && EMAIL_RE.test(v);

/** Chuẩn hoá số điện thoại Việt Nam về dạng 0xxxxxxxxx. */
function normalizePhone(value) {
  const text = cleanText(value);
  if (!text) return '';
  let digits = text.replace(/[\s.\-()]/g, '');
  if (digits.startsWith('+84')) digits = '0' + digits.slice(3);
  else if (digits.startsWith('84') && digits.length === 11) digits = '0' + digits.slice(2);
  else if (/^[1-9]\d{8}$/.test(digits)) digits = '0' + digits; // Excel làm mất số 0 đầu
  return digits;
}
const isValidPhone = (v) => PHONE_RE.test(v || '');

function isValidDate(value) {
  if (typeof value !== 'string' || !DATE_RE.test(value)) return false;
  const d = new Date(value + 'T00:00:00Z');
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value;
}

/** Trả về số >= 0 (làm tròn 2 chữ số) hoặc null nếu không hợp lệ. */
function parseMoney(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return null;
  const n = Number(String(value).replace(/,/g, '').trim());
  if (!Number.isFinite(n) || n < 0) return null;
  return Math.round(n * 100) / 100;
}

function stripAccents(text) {
  return String(text || '').replace(/đ/g, 'd').replace(/Đ/g, 'D').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}
const normalizeKey = (text) => stripAccents(text).toLowerCase().replace(/[^a-z0-9]/g, '');

function parseOptionalId(value, field) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  if (!Number.isInteger(n) || n <= 0) {
    throw new ApiError(422, 'Dữ liệu chưa hợp lệ', { [field]: `${field} phải là số nguyên dương` });
  }
  return n;
}

const truthy = (v) => v === true || ['1', 'true', 'yes', 'co', 'có'].includes(String(v).trim().toLowerCase());
const pct = (part, whole) => (whole ? Math.round((part * 10000) / whole) / 100 : 0);
const round2 = (n) => Math.round(n * 100) / 100;

module.exports = {
  ApiError, nowIso, cleanText, normalizeEmail, isValidEmail, normalizePhone, isValidPhone,
  isValidDate, parseMoney, stripAccents, normalizeKey, parseOptionalId, truthy, pct, round2,
};
