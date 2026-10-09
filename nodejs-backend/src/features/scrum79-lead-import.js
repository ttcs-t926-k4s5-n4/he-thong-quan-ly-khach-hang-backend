'use strict';
/**
 * SCRUM-79 — Là Nhân viên Marketing, tôi muốn tạo lead thủ công và nhập lead hàng loạt từ Excel,
 * để đưa danh sách thu được từ hội thảo vào hệ thống ngay hôm sau.
 *
 * Chức năng:
 *  - Nhập tay một lead (từ sự kiện, danh thiếp...) — bắt buộc có nguồn, cảnh báo trùng.
 *  - Tải tệp mẫu Excel.
 *  - Nhập hàng loạt 2 bước: (1) xem trước + báo lỗi theo từng dòng, (2) xác nhận nhập.
 *  - Mọi lead nhập vào đều bắt buộc có nguồn (cột "Nguồn" hoặc nguồn mặc định của lô).
 */
const path = require('path');
const { LEAD_SOURCES, LEAD_STATUS_NEW, MANUAL_SOURCES } = require('../core/constants');
const {
  ApiError, cleanText, nowIso, normalizeEmail, isValidEmail, normalizePhone, isValidPhone,
  normalizeKey, parseOptionalId, truthy,
} = require('../core/utils');
const {
  insertLead, findDuplicateLead, resolveCampaignId, getLeadOr404, leadToDto,
} = require('../core/leads');
const { readXlsx, writeXlsx, readCsv } = require('../core/xlsx');

const FEATURE = {
  key: 'SCRUM-79',
  branch: 'feature/SCRUM-79-lead-import-excel-backend',
  name: 'Tạo lead thủ công và nhập lead hàng loạt từ Excel',
};

const TEMPLATE_HEADERS = ['Họ tên*', 'Email', 'Số điện thoại', 'Công ty', 'Nhu cầu quan tâm', 'Nguồn', 'Chi tiết nguồn', 'Ghi chú'];

const HEADER_ALIASES = {
  full_name: ['hoten', 'hovaten', 'ten', 'tenkhachhang', 'fullname', 'name'],
  email: ['email', 'thudientu', 'mail'],
  phone: ['sodienthoai', 'sdt', 'dienthoai', 'phone', 'mobile', 'didong'],
  company: ['congty', 'tencongty', 'company', 'donvi'],
  interest: ['nhucauquantam', 'nhucau', 'quantam', 'interest'],
  source: ['nguon', 'nguonlead', 'source'],
  source_detail: ['chitietnguon', 'tensukien', 'sukien', 'sourcedetail'],
  note: ['ghichu', 'note'],
};
const HEADER_LOOKUP = {};
for (const [field, aliases] of Object.entries(HEADER_ALIASES)) aliases.forEach((a) => { HEADER_LOOKUP[a] = field; });

const SOURCE_LOOKUP = {};
for (const code of MANUAL_SOURCES) {
  SOURCE_LOOKUP[normalizeKey(code)] = code;
  SOURCE_LOOKUP[normalizeKey(LEAD_SOURCES[code])] = code;
}
const SOURCE_HINT = MANUAL_SOURCES.map((c) => LEAD_SOURCES[c]).join(', ');
const FIELD_LIMITS = { company: 200, interest: 2000, note: 2000, source_detail: 200 };

// --------------------------------------------- kiểm tra dữ liệu một lead ----
function validateLeadInput(raw, defaultSource = '', defaultDetail = '') {
  const values = {};
  const errors = {};
  const fullName = cleanText(raw.full_name);
  if (!fullName) errors.full_name = 'Họ tên là bắt buộc';
  else if (fullName.length > 150) errors.full_name = 'Họ tên tối đa 150 ký tự';
  values.full_name = fullName;

  const email = normalizeEmail(raw.email);
  if (email && !isValidEmail(email)) errors.email = `Email '${email}' không hợp lệ`;
  values.email = email;

  const phoneRaw = cleanText(raw.phone);
  const phone = normalizePhone(phoneRaw);
  if (phoneRaw && !isValidPhone(phone)) errors.phone = `Số điện thoại '${phoneRaw}' không hợp lệ (VD: 0912345678)`;
  values.phone = phoneRaw ? phone : '';

  if (!email && !phoneRaw) errors.contact = 'Cần ít nhất email hoặc số điện thoại';

  for (const [field, limit] of Object.entries(FIELD_LIMITS)) {
    const value = cleanText(raw[field], field === 'interest' || field === 'note');
    if (value.length > limit) errors[field] = `Tối đa ${limit} ký tự`;
    values[field] = value;
  }

  const sourceRaw = cleanText(raw.source) || cleanText(defaultSource);
  values.source = '';
  if (!sourceRaw) {
    errors.source = `Nguồn là bắt buộc. Chọn một trong: ${SOURCE_HINT}`;
  } else {
    const code = SOURCE_LOOKUP[normalizeKey(sourceRaw)];
    if (!code) errors.source = `Nguồn '${sourceRaw}' không hợp lệ. Chọn một trong: ${SOURCE_HINT}`;
    values.source = code || sourceRaw;
  }
  if (!values.source_detail) values.source_detail = cleanText(defaultDetail);
  return { values, errors };
}

const expiresAt = (createdAt, config) => new Date(Date.parse(createdAt) + config.IMPORT_PREVIEW_TTL_MINUTES * 60000);

function batchToDto(batch, config) {
  const { rows, ...rest } = batch;
  return {
    ...rest,
    source_label: LEAD_SOURCES[batch.default_source] || null,
    expires_at: expiresAt(batch.created_at, config).toISOString().replace(/\.\d{3}Z$/, 'Z'),
    rows,
    errors: rows.flatMap((r) => r.errors.map((e) => ({ row_number: r.row_number, ...e }))),
  };
}

function getBatchOr404(db, id) {
  const batch = db.get('import_batches', id);
  if (!batch) throw new ApiError(404, `Không tìm thấy lô nhập #${id}`);
  return batch;
}

// ------------------------------------------------------------------ routes
function register(router) {
  // ---- Nhập tay một lead ----
  router.post('/api/leads', ({ db, body, userId }) => {
    const { values, errors } = validateLeadInput(body);
    const campaign = resolveCampaignId(db, body.campaign_id);
    if (campaign.error) errors.campaign_id = campaign.error;
    if (Object.keys(errors).length) throw new ApiError(422, 'Dữ liệu lead chưa hợp lệ', errors);

    const dup = findDuplicateLead(db, values.email, values.phone);
    if (dup && !truthy(body.allow_duplicate)) {
      throw new ApiError(409,
        `Lead đã tồn tại (#${dup.id} - ${dup.full_name}). Gửi allow_duplicate=true nếu vẫn muốn tạo.`,
        { duplicate_lead_id: dup.id });
    }
    const lead = insertLead(db, { ...values, status: LEAD_STATUS_NEW, campaign_id: campaign.id, created_by: userId });
    return { status: 201, json: leadToDto(getLeadOr404(db, lead.id)) };
  });

  // ---- Tệp mẫu ----
  router.get('/api/leads/import/template', () => {
    const guide = [
      ['Hướng dẫn nhập lead'],
      ["1. Điền dữ liệu từ dòng 2 của sheet 'Danh sách lead', không đổi tên cột."],
      ['2. Bắt buộc: Họ tên và ít nhất một trong Email / Số điện thoại.'],
      ['3. Cột Nguồn: để trống nếu đã chọn nguồn mặc định khi tải tệp lên.'],
      ['4. Hệ thống sẽ xem trước và báo lỗi theo từng dòng trước khi nhập thật.'],
      [''],
      ['Giá trị hợp lệ cho cột Nguồn:'],
      ...MANUAL_SOURCES.map((c) => [LEAD_SOURCES[c], c]),
    ];
    const buffer = writeXlsx([
      { name: 'Danh sách lead', rows: [TEMPLATE_HEADERS], widths: [26, 30, 16, 28, 40, 16, 28, 30], boldHeader: true },
      { name: 'Hướng dẫn', rows: guide, widths: [70, 16] },
    ]);
    return {
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      headers: { 'Content-Disposition': 'attachment; filename="mau-nhap-lead.xlsx"' },
      body: buffer,
    };
  });

  // ---- Bước 1: tải tệp & xem trước ----
  router.post('/api/leads/import/preview', ({ db, body, files, config, userId }) => {
    const upload = files.file;
    if (!upload || !upload.filename) throw new ApiError(400, "Vui lòng chọn tệp Excel (.xlsx) hoặc CSV ở trường 'file'");
    const ext = path.extname(upload.filename).toLowerCase();
    if (!['.xlsx', '.xlsm', '.csv'].includes(ext)) throw new ApiError(400, 'Chỉ hỗ trợ tệp .xlsx hoặc .csv');
    if (!upload.data.length) throw new ApiError(400, 'Tệp rỗng');

    const errors = {};
    let defaultSource = cleanText(body.default_source);
    if (defaultSource) {
      const code = SOURCE_LOOKUP[normalizeKey(defaultSource)];
      if (!code) errors.default_source = `Nguồn mặc định không hợp lệ. Chọn một trong: ${SOURCE_HINT}`;
      defaultSource = code || '';
    }
    const defaultDetail = cleanText(body.source_detail);
    const campaign = resolveCampaignId(db, body.campaign_id);
    if (campaign.error) errors.campaign_id = campaign.error;
    if (Object.keys(errors).length) throw new ApiError(422, 'Thông tin lô nhập chưa hợp lệ', errors);

    let table;
    try {
      table = ext === '.csv' ? readCsv(upload.data) : readXlsx(upload.data);
    } catch (e) {
      throw new ApiError(400, 'Không đọc được tệp. Hãy dùng đúng tệp mẫu (.xlsx) hoặc CSV UTF-8.');
    }
    if (!table.length) throw new ApiError(400, 'Tệp không có dữ liệu');

    const mapping = {};
    const ignored = [];
    table[0].forEach((header, index) => {
      const field = HEADER_LOOKUP[normalizeKey(header)];
      if (field && !Object.values(mapping).includes(field)) mapping[index] = field;
      else if (cleanText(header)) ignored.push(cleanText(header));
    });
    const fields = new Set(Object.values(mapping));
    if (!fields.has('full_name')) throw new ApiError(400, "Thiếu cột bắt buộc 'Họ tên'. Hãy tải tệp mẫu để dùng đúng định dạng.");
    if (!fields.has('email') && !fields.has('phone')) throw new ApiError(400, "Tệp cần có ít nhất cột 'Email' hoặc 'Số điện thoại'");

    const dataRows = table.slice(1)
      .map((row, i) => ({ rowNumber: i + 2, row }))
      .filter(({ row }) => row.some((c) => cleanText(c)));
    if (!dataRows.length) throw new ApiError(400, 'Tệp không có dòng dữ liệu nào');
    if (dataRows.length > config.MAX_IMPORT_ROWS) {
      throw new ApiError(400, `Mỗi lần chỉ nhập tối đa ${config.MAX_IMPORT_ROWS} dòng (tệp có ${dataRows.length} dòng)`);
    }

    const seenEmail = {};
    const seenPhone = {};
    const results = dataRows.map(({ rowNumber, row }) => {
      const raw = {};
      for (const [i, field] of Object.entries(mapping)) raw[field] = row[Number(i)] || '';
      const { values, errors: errs } = validateLeadInput(raw, defaultSource, defaultDetail);
      const rowErrors = Object.entries(errs).map(([field, message]) => ({ field, message }));
      const email = errs.email ? '' : values.email;
      const phone = errs.phone ? '' : values.phone;
      if (email) {
        if (seenEmail[email]) rowErrors.push({ field: 'email', message: `Email trùng với dòng ${seenEmail[email]} trong tệp` });
        else seenEmail[email] = rowNumber;
      }
      if (phone) {
        if (seenPhone[phone]) rowErrors.push({ field: 'phone', message: `SĐT trùng với dòng ${seenPhone[phone]} trong tệp` });
        else seenPhone[phone] = rowNumber;
      }
      const dup = findDuplicateLead(db, email, phone);
      if (dup) {
        rowErrors.push({
          field: email && dup.email === email ? 'email' : 'phone',
          message: `Đã tồn tại trong hệ thống (lead #${dup.id} - ${dup.full_name})`,
        });
      }
      values.source_label = LEAD_SOURCES[values.source] || null;
      return { row_number: rowNumber, valid: rowErrors.length === 0, data: values, errors: rowErrors };
    });

    const validCount = results.filter((r) => r.valid).length;
    const batch = db.insert('import_batches', {
      file_name: upload.filename,
      default_source: defaultSource || null,
      source_detail: defaultDetail || null,
      campaign_id: campaign.id,
      total_rows: results.length,
      valid_rows: validCount,
      error_rows: results.length - validCount,
      imported_count: 0,
      status: 'preview',
      rows: results,
      created_by: userId,
      created_at: nowIso(),
      committed_at: null,
    });
    return {
      status: 201,
      json: {
        ...batchToDto(batch, config),
        preview_id: batch.id,
        ignored_columns: ignored,
        message: `Đọc được ${results.length} dòng: ${validCount} hợp lệ, ${results.length - validCount} lỗi. `
          + 'Kiểm tra rồi gọi API xác nhận để nhập.',
      },
    };
  });

  router.get('/api/leads/import/:id', ({ db, params, config }) => {
    const batch = getBatchOr404(db, parseOptionalId(params.id, 'id'));
    return { json: batchToDto(batch, config) };
  });

  // ---- Bước 2: xác nhận nhập ----
  router.post('/api/leads/import/:id/commit', ({ db, params, body, config, userId }) => {
    const id = parseOptionalId(params.id, 'id');
    const batch = getBatchOr404(db, id);
    if (batch.status === 'committed') throw new ApiError(409, 'Lô nhập này đã được xác nhận trước đó');
    if (Date.now() > expiresAt(batch.created_at, config).getTime()) {
      throw new ApiError(410, 'Bản xem trước đã hết hạn, vui lòng tải tệp lên lại');
    }
    const mode = cleanText(body.mode) || 'valid_only';
    if (!['valid_only', 'all_or_nothing'].includes(mode)) throw new ApiError(422, "mode phải là 'valid_only' hoặc 'all_or_nothing'");
    if (mode === 'all_or_nothing' && batch.error_rows > 0) {
      throw new ApiError(422, `Tệp còn ${batch.error_rows} dòng lỗi. Sửa tệp hoặc dùng mode 'valid_only'.`);
    }

    const result = db.transaction(() => {
      const imported = [];
      const skipped = [];
      for (const row of batch.rows) {
        if (!row.valid) {
          skipped.push({ row_number: row.row_number, reason: row.errors.map((e) => e.message).join('; ') });
          continue;
        }
        const dup = findDuplicateLead(db, row.data.email, row.data.phone);
        if (dup) {
          skipped.push({ row_number: row.row_number, reason: `Đã tồn tại trong hệ thống (lead #${dup.id})` });
          continue;
        }
        const { source_label: _ignored, ...data } = row.data;
        const lead = insertLead(db, {
          ...data, status: LEAD_STATUS_NEW, campaign_id: batch.campaign_id, import_batch_id: id, created_by: userId,
        });
        imported.push({ row_number: row.row_number, lead_id: lead.id });
      }
      db.update('import_batches', id, { status: 'committed', committed_at: nowIso(), imported_count: imported.length });
      return { imported, skipped };
    });

    return {
      status: 201,
      json: {
        message: `Đã nhập ${result.imported.length} lead, bỏ qua ${result.skipped.length} dòng.`,
        batch_id: id,
        imported_count: result.imported.length,
        skipped_count: result.skipped.length,
        imported: result.imported,
        skipped: result.skipped,
      },
    };
  });
}

module.exports = { FEATURE, register, validateLeadInput };
