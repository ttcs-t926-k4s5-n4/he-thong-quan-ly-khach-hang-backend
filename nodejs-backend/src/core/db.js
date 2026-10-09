'use strict';
/**
 * Kho dữ liệu JSON đơn giản (không cần cài CSDL) — đủ dùng cho chạy thử & demo.
 * Ghi file theo kiểu atomic (ghi tệp tạm rồi rename). DB_PATH=":memory:" để chỉ lưu trong RAM.
 * Có thể thay bằng PostgreSQL/MySQL sau này mà không đổi API vì feature chỉ dùng các hàm bên dưới.
 */
const fs = require('fs');
const path = require('path');

const TABLES = ['campaigns', 'web_forms', 'import_batches', 'leads', 'opportunities'];

class JsonStore {
  constructor(filePath) {
    this.filePath = filePath;
    this.inTransaction = false;
    this.data = { seq: {}, ...Object.fromEntries(TABLES.map((t) => [t, []])) };
    if (filePath !== ':memory:') {
      fs.mkdirSync(path.dirname(path.resolve(filePath)), { recursive: true });
      if (fs.existsSync(filePath)) {
        const loaded = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        this.data = { ...this.data, ...loaded };
      }
    }
  }

  save() {
    if (this.filePath === ':memory:' || this.inTransaction) return;
    const tmp = `${this.filePath}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(this.data, null, 2), 'utf8');
    fs.renameSync(tmp, this.filePath);
  }

  /** Chạy fn như một giao dịch: lỗi giữa chừng -> khôi phục dữ liệu như trước. */
  transaction(fn) {
    const snapshot = JSON.stringify(this.data);
    this.inTransaction = true;
    try {
      const result = fn();
      this.inTransaction = false;
      this.save();
      return result;
    } catch (err) {
      this.data = JSON.parse(snapshot);
      this.inTransaction = false;
      throw err;
    }
  }

  insert(table, record) {
    const id = (this.data.seq[table] || 0) + 1;
    this.data.seq[table] = id;
    const row = { id, ...record };
    this.data[table].push(row);
    this.save();
    return { ...row };
  }

  update(table, id, patch) {
    const row = this.data[table].find((r) => r.id === id);
    if (!row) return null;
    Object.assign(row, patch);
    this.save();
    return { ...row };
  }

  get(table, id) {
    const row = this.data[table].find((r) => r.id === Number(id));
    return row ? { ...row } : null;
  }

  findOne(table, predicate) {
    const row = this.data[table].find(predicate);
    return row ? { ...row } : null;
  }

  filter(table, predicate = () => true) {
    return this.data[table].filter(predicate).map((r) => ({ ...r }));
  }

  count(table, predicate = () => true) {
    return this.data[table].filter(predicate).length;
  }
}

module.exports = { JsonStore };
