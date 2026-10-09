'use strict';
/**
 * Đọc / ghi tệp Excel .xlsx tối giản, chỉ dùng thư viện có sẵn của Node (zlib).
 * .xlsx thực chất là tệp ZIP chứa các tệp XML — đủ cho nhu cầu nhập/xuất danh sách lead.
 */
const zlib = require('zlib');

// ---------------------------------------------------------------- ZIP ----
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i += 1) crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function readZip(buffer) {
  let eocd = -1;
  for (let i = buffer.length - 22; i >= Math.max(0, buffer.length - 65557); i -= 1) {
    if (buffer.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd === -1) throw new Error('Không phải tệp ZIP/XLSX hợp lệ');
  const entries = buffer.readUInt16LE(eocd + 10);
  let ptr = buffer.readUInt32LE(eocd + 16);
  const files = {};
  for (let i = 0; i < entries; i += 1) {
    if (buffer.readUInt32LE(ptr) !== 0x02014b50) throw new Error('ZIP hỏng');
    const method = buffer.readUInt16LE(ptr + 10);
    const compSize = buffer.readUInt32LE(ptr + 20);
    const nameLen = buffer.readUInt16LE(ptr + 28);
    const extraLen = buffer.readUInt16LE(ptr + 30);
    const commentLen = buffer.readUInt16LE(ptr + 32);
    const localOffset = buffer.readUInt32LE(ptr + 42);
    const name = buffer.slice(ptr + 46, ptr + 46 + nameLen).toString('utf8');
    const lNameLen = buffer.readUInt16LE(localOffset + 26);
    const lExtraLen = buffer.readUInt16LE(localOffset + 28);
    const start = localOffset + 30 + lNameLen + lExtraLen;
    const raw = buffer.slice(start, start + compSize);
    files[name] = () => (method === 8 ? zlib.inflateRawSync(raw) : raw);
    ptr += 46 + nameLen + extraLen + commentLen;
  }
  return files;
}

function writeZip(entries) {
  const locals = [];
  const centrals = [];
  let offset = 0;
  for (const { name, data } of entries) {
    const nameBuf = Buffer.from(name, 'utf8');
    const content = Buffer.isBuffer(data) ? data : Buffer.from(data, 'utf8');
    const compressed = zlib.deflateRawSync(content);
    const crc = crc32(content);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0x0800, 6); // tên tệp UTF-8
    local.writeUInt16LE(8, 8);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(compressed.length, 18);
    local.writeUInt32LE(content.length, 22);
    local.writeUInt16LE(nameBuf.length, 26);
    locals.push(local, nameBuf, compressed);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0x0800, 8);
    central.writeUInt16LE(8, 10);
    central.writeUInt32LE(crc, 16);
    central.writeUInt32LE(compressed.length, 20);
    central.writeUInt32LE(content.length, 24);
    central.writeUInt16LE(nameBuf.length, 28);
    central.writeUInt32LE(offset, 42);
    centrals.push(central, nameBuf);
    offset += 30 + nameBuf.length + compressed.length;
  }
  const centralBuf = Buffer.concat(centrals);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralBuf.length, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, centralBuf, end]);
}

// ---------------------------------------------------------------- XML ----
const decodeXml = (s) => s
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'")
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&amp;/g, '&');
const encodeXml = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '');

const textOf = (xml) => {
  let out = '';
  const re = /<(?:\w+:)?t(?:\s[^>]*)?>([\s\S]*?)<\/(?:\w+:)?t>/g;
  let m;
  while ((m = re.exec(xml))) out += decodeXml(m[1]);
  return out;
};

function columnIndex(ref) {
  const letters = /^[A-Z]+/.exec(ref)[0];
  let n = 0;
  for (const ch of letters) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}
const columnName = (index) => {
  let n = index + 1;
  let s = '';
  while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); }
  return s;
};

function formatNumber(raw) {
  const n = Number(raw);
  return Number.isFinite(n) ? String(n) : raw;
}

/** Đọc sheet đầu tiên của tệp .xlsx -> mảng các dòng (mỗi dòng là mảng chuỗi). */
function readXlsx(buffer) {
  const files = readZip(buffer);
  const load = (name) => (files[name] ? files[name]().toString('utf8') : null);

  const shared = [];
  const sst = load('xl/sharedStrings.xml');
  if (sst) {
    const re = /<si>([\s\S]*?)<\/si>/g;
    let m;
    while ((m = re.exec(sst))) shared.push(textOf(m[1]));
  }

  let sheetPath = 'xl/worksheets/sheet1.xml';
  const workbook = load('xl/workbook.xml');
  const rels = load('xl/_rels/workbook.xml.rels');
  if (workbook && rels) {
    const firstSheet = /<sheet\b[^>]*\br:id="([^"]+)"/.exec(workbook);
    if (firstSheet) {
      const relRe = new RegExp(`<Relationship\\b[^>]*Id="${firstSheet[1]}"[^>]*/?>`);
      const rel = relRe.exec(rels);
      const target = rel && /Target="([^"]+)"/.exec(rel[0]);
      if (target) sheetPath = target[1].startsWith('/') ? target[1].slice(1) : `xl/${target[1].replace(/^\.\//, '')}`;
    }
  }
  const sheet = load(sheetPath);
  if (!sheet) throw new Error('Không tìm thấy sheet dữ liệu');

  const rows = [];
  const rowRe = /<row\b([^>]*?)(?:\/>|>([\s\S]*?)<\/row>)/g;
  let rm;
  while ((rm = rowRe.exec(sheet))) {
    const rIndexMatch = /\br="(\d+)"/.exec(rm[1]);
    const rowIndex = rIndexMatch ? Number(rIndexMatch[1]) - 1 : rows.length;
    const cells = [];
    const cellRe = /<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g;
    let cm;
    let col = 0;
    while ((cm = cellRe.exec(rm[2] || ''))) {
      const attrs = cm[1];
      const ref = /\br="([A-Z]+\d+)"/.exec(attrs);
      if (ref) col = columnIndex(ref[1]);
      const type = (/\bt="(\w+)"/.exec(attrs) || [])[1];
      const inner = cm[2] || '';
      const v = /<v>([\s\S]*?)<\/v>/.exec(inner);
      let value = '';
      if (type === 's' && v) value = shared[Number(v[1])] || '';
      else if (type === 'inlineStr') value = textOf(inner);
      else if (type === 'b' && v) value = v[1] === '1' ? 'TRUE' : 'FALSE';
      else if (type === 'str' && v) value = decodeXml(v[1]);
      else if (v) value = formatNumber(decodeXml(v[1]));
      cells[col] = String(value).trim();
      col += 1;
    }
    for (let i = 0; i < cells.length; i += 1) if (cells[i] === undefined) cells[i] = '';
    rows[rowIndex] = cells;
  }
  for (let i = 0; i < rows.length; i += 1) if (!rows[i]) rows[i] = [];
  return rows;
}

/**
 * Tạo tệp .xlsx. sheets = [{ name, rows: [[...]], widths?: [số], boldHeader?: bool }]
 */
function writeXlsx(sheets) {
  const sheetXml = (sheet) => {
    const cols = sheet.widths
      ? `<cols>${sheet.widths.map((w, i) => `<col min="${i + 1}" max="${i + 1}" width="${w}" customWidth="1"/>`).join('')}</cols>`
      : '';
    const rows = sheet.rows.map((row, r) => {
      const cells = row.map((value, c) => {
        if (value === null || value === undefined || value === '') return '';
        const ref = `${columnName(c)}${r + 1}`;
        const style = sheet.boldHeader && r === 0 ? ' s="1"' : '';
        return `<c r="${ref}" t="inlineStr"${style}><is><t xml:space="preserve">${encodeXml(value)}</t></is></c>`;
      }).join('');
      return `<row r="${r + 1}">${cells}</row>`;
    }).join('');
    const freeze = sheet.boldHeader
      ? '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
      : '';
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
      + `${freeze}${cols}<sheetData>${rows}</sheetData></worksheet>`;
  };

  const entries = [
    {
      name: '[Content_Types].xml',
      data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        + '<Default Extension="xml" ContentType="application/xml"/>'
        + '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + sheets.map((_, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('')
        + '</Types>',
    },
    {
      name: '_rels/.rels',
      data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        + '</Relationships>',
    },
    {
      name: 'xl/workbook.xml',
      data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        + 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + sheets.map((s, i) => `<sheet name="${encodeXml(s.name)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join('')
        + '</sheets></workbook>',
    },
    {
      name: 'xl/_rels/workbook.xml.rels',
      data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + sheets.map((_, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join('')
        + `<Relationship Id="rId${sheets.length + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>`
        + '</Relationships>',
    },
    {
      name: 'xl/styles.xml',
      data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        + '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
        + '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
        + '<fill><patternFill patternType="solid"><fgColor rgb="FF1F6FEB"/><bgColor indexed="64"/></patternFill></fill></fills>'
        + '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        + '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        + '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
        + '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        + '</styleSheet>',
    },
    ...sheets.map((s, i) => ({ name: `xl/worksheets/sheet${i + 1}.xml`, data: sheetXml(s) })),
  ];
  return writeZip(entries);
}

/** Đọc CSV (tự nhận dấu phân cách , ; hoặc tab, hỗ trợ ngoặc kép). */
function readCsv(buffer) {
  const text = buffer.toString('utf8').replace(/^\uFEFF/, '');
  const firstLine = text.split(/\r?\n/)[0] || '';
  const delimiter = [';', '\t', ','].reduce((best, d) => (
    firstLine.split(d).length > firstLine.split(best).length ? d : best), ',');
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) { row.push(field.trim()); field = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i += 1;
      row.push(field.trim()); rows.push(row); row = []; field = '';
    } else field += ch;
  }
  if (field || row.length) { row.push(field.trim()); rows.push(row); }
  return rows;
}

module.exports = { readXlsx, writeXlsx, readCsv };
