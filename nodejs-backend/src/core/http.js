'use strict';
/** Router & bộ đọc body tối giản trên module http có sẵn của Node (không cần Express). */
const { ApiError } = require('./utils');

class Router {
  constructor() { this.routes = []; }

  add(method, pattern, handler) {
    const keys = [];
    const regex = new RegExp('^' + pattern.replace(/\./g, '\\.').replace(/:(\w+)/g, (_, k) => {
      keys.push(k);
      return '([^/]+?)';
    }) + '/?$');
    this.routes.push({ method, regex, keys, handler });
  }

  get(p, h) { this.add('GET', p, h); }
  post(p, h) { this.add('POST', p, h); }
  patch(p, h) { this.add('PATCH', p, h); }

  match(method, pathname) {
    let pathMatched = false;
    for (const r of this.routes) {
      const m = r.regex.exec(pathname);
      if (!m) continue;
      pathMatched = true;
      if (r.method !== method) continue;
      const params = {};
      r.keys.forEach((k, i) => { params[k] = decodeURIComponent(m[i + 1]); });
      return { handler: r.handler, params };
    }
    return pathMatched ? { methodNotAllowed: true } : null;
  }
}

function readBody(req, limitBytes) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    let tooLarge = false;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > limitBytes) { tooLarge = true; return; }
      chunks.push(chunk);
    });
    req.on('end', () => (tooLarge
      ? reject(new ApiError(413, 'Tệp hoặc dữ liệu gửi lên vượt quá dung lượng cho phép (tối đa 5MB)'))
      : resolve(Buffer.concat(chunks))));
    req.on('error', reject);
  });
}

function parseMultipart(buffer, boundary) {
  const fields = {};
  const files = {};
  const delimiter = Buffer.from(`--${boundary}`);
  let pos = buffer.indexOf(delimiter);
  while (pos !== -1) {
    pos += delimiter.length;
    if (buffer.slice(pos, pos + 2).toString() === '--') break;
    pos += 2; // CRLF
    const headerEnd = buffer.indexOf('\r\n\r\n', pos);
    if (headerEnd === -1) break;
    const headerText = buffer.slice(pos, headerEnd).toString('utf8');
    const next = buffer.indexOf(delimiter, headerEnd + 4);
    if (next === -1) break;
    const content = buffer.slice(headerEnd + 4, next - 2);
    const name = /name="([^"]*)"/i.exec(headerText);
    const filename = /filename="([^"]*)"/i.exec(headerText);
    if (name) {
      if (filename) files[name[1]] = { filename: filename[1], data: content };
      else fields[name[1]] = content.toString('utf8');
    }
    pos = next;
  }
  return { fields, files };
}

async function parseRequestBody(req, limitBytes) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return { body: {}, files: {} };
  const raw = await readBody(req, limitBytes);
  if (!raw.length) return { body: {}, files: {} };
  const type = (req.headers['content-type'] || '').toLowerCase();
  if (type.includes('multipart/form-data')) {
    const boundary = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(req.headers['content-type']);
    if (!boundary) throw new ApiError(400, 'Thiếu boundary trong multipart/form-data');
    const { fields, files } = parseMultipart(raw, boundary[1] || boundary[2]);
    return { body: fields, files };
  }
  if (type.includes('application/x-www-form-urlencoded')) {
    return { body: Object.fromEntries(new URLSearchParams(raw.toString('utf8'))), files: {} };
  }
  let body;
  try {
    body = JSON.parse(raw.toString('utf8'));
  } catch (e) {
    throw new ApiError(400, 'Nội dung JSON không hợp lệ');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw new ApiError(400, 'Nội dung gửi lên phải là một đối tượng JSON');
  }
  return { body, files: {} };
}

function sendJson(res, status, payload, headers = {}) {
  const text = JSON.stringify(payload);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', ...headers });
  res.end(text);
}

module.exports = { Router, parseRequestBody, sendJson };
