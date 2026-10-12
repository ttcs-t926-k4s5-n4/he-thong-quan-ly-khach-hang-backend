-- Lược đồ CSDL CRM: cơ hội bán hàng, pipeline, dòng sản phẩm, điều kiện chuyển giai đoạn,
-- hoạt động với khách hàng và công việc. Thời gian lưu theo giờ Việt Nam (UTC+7),
-- dạng 'YYYY-MM-DD HH:MM:SS'; ngày lưu dạng 'YYYY-MM-DD'; tiền lưu số nguyên (đồng).
PRAGMA foreign_keys = ON;

-- ======================= DÙNG CHUNG =======================
CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    leader_id   INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    full_name      TEXT NOT NULL,
    email          TEXT,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('staff', 'team_lead', 'director', 'admin')),
    team_id        INTEGER REFERENCES teams(id),
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    tax_code    TEXT,
    phone       TEXT,
    email       TEXT,
    address     TEXT,
    owner_id    INTEGER NOT NULL REFERENCES users(id),
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customers_owner ON customers(owner_id);

CREATE TABLE IF NOT EXISTS contacts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    full_name    TEXT NOT NULL,
    job_title    TEXT,
    phone        TEXT,
    email        TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_contacts_customer ON contacts(customer_id);

-- Giai đoạn pipeline: xác suất thắng mặc định và ngưỡng ngày cảnh báo đình trệ
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    code                 TEXT NOT NULL UNIQUE,
    name                 TEXT NOT NULL,
    sort_order           INTEGER NOT NULL,
    default_probability  INTEGER NOT NULL CHECK (default_probability BETWEEN 0 AND 100),
    stale_after_days     INTEGER,
    is_won               INTEGER NOT NULL DEFAULT 0,
    is_lost              INTEGER NOT NULL DEFAULT 0,
    is_active            INTEGER NOT NULL DEFAULT 1
);

-- Danh mục sản phẩm / dịch vụ và bảng giá niêm yết
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    product_type    TEXT NOT NULL CHECK (product_type IN ('product', 'service', 'subscription')),
    unit            TEXT NOT NULL,
    billing_period  TEXT CHECK (billing_period IN ('month', 'quarter', 'year')),
    description     TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS price_lists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    is_default  INTEGER NOT NULL DEFAULT 0,
    valid_from  TEXT NOT NULL,
    valid_to    TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS price_list_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    price_list_id  INTEGER NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    product_id     INTEGER NOT NULL REFERENCES products(id),
    unit_price     INTEGER NOT NULL CHECK (unit_price >= 0),
    UNIQUE (price_list_id, product_id)
);

-- ======================= SCRUM-87: CƠ HỘI BÁN HÀNG =======================
CREATE TABLE IF NOT EXISTS opportunities (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    customer_id             INTEGER NOT NULL REFERENCES customers(id),
    primary_contact_id      INTEGER REFERENCES contacts(id),
    stage_id                INTEGER NOT NULL REFERENCES pipeline_stages(id),
    estimated_value         INTEGER NOT NULL DEFAULT 0 CHECK (estimated_value >= 0),
    amount                  INTEGER NOT NULL DEFAULT 0 CHECK (amount >= 0),
    amount_source           TEXT NOT NULL DEFAULT 'manual' CHECK (amount_source IN ('manual', 'lines')),
    recurring_annual_value  INTEGER NOT NULL DEFAULT 0,
    expected_close_date     TEXT NOT NULL,
    source                  TEXT NOT NULL DEFAULT 'other',
    description             TEXT,
    probability             INTEGER NOT NULL CHECK (probability BETWEEN 0 AND 100),
    probability_is_manual   INTEGER NOT NULL DEFAULT 0,
    probability_note        TEXT,
    owner_id                INTEGER NOT NULL REFERENCES users(id),
    stage_entered_at        TEXT NOT NULL,
    closed_at               TEXT,
    is_deleted              INTEGER NOT NULL DEFAULT 0,
    created_by              INTEGER NOT NULL REFERENCES users(id),
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opp_customer ON opportunities(customer_id);
CREATE INDEX IF NOT EXISTS idx_opp_owner ON opportunities(owner_id);
