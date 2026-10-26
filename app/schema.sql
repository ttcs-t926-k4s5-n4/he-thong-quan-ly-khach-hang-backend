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
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until   TEXT,
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
CREATE INDEX IF NOT EXISTS idx_opp_stage ON opportunities(stage_id);
CREATE INDEX IF NOT EXISTS idx_opp_close_date ON opportunities(expected_close_date);

-- Lịch sử chuyển giai đoạn (kèm thông tin ghi đè điều kiện – SCRUM-90)
CREATE TABLE IF NOT EXISTS opportunity_stage_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id    INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    from_stage_id     INTEGER REFERENCES pipeline_stages(id),
    to_stage_id       INTEGER NOT NULL REFERENCES pipeline_stages(id),
    changed_by        INTEGER NOT NULL REFERENCES users(id),
    changed_at        TEXT NOT NULL,
    is_override       INTEGER NOT NULL DEFAULT 0,
    override_reason   TEXT,
    unmet_conditions  TEXT
);
CREATE INDEX IF NOT EXISTS idx_stage_history_opp ON opportunity_stage_history(opportunity_id);

-- ======================= SCRUM-89: DÒNG SẢN PHẨM CỦA CƠ HỘI =======================
CREATE TABLE IF NOT EXISTS opportunity_lines (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id    INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    product_id        INTEGER NOT NULL REFERENCES products(id),
    product_code      TEXT NOT NULL,
    product_name      TEXT NOT NULL,
    product_type      TEXT NOT NULL,
    unit              TEXT NOT NULL,
    quantity          REAL NOT NULL CHECK (quantity > 0),
    list_price        INTEGER,
    unit_price        INTEGER NOT NULL CHECK (unit_price >= 0),
    discount_percent  REAL NOT NULL DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    billing_period    TEXT,
    periods           INTEGER,
    line_total        INTEGER NOT NULL,
    annual_value      INTEGER,
    note              TEXT,
    created_by        INTEGER NOT NULL REFERENCES users(id),
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lines_opp ON opportunity_lines(opportunity_id);

-- ======================= SCRUM-90: ĐIỀU KIỆN KHI RỜI GIAI ĐOẠN =======================
CREATE TABLE IF NOT EXISTS stage_exit_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id        INTEGER NOT NULL REFERENCES pipeline_stages(id),
    rule_type       TEXT NOT NULL CHECK (rule_type IN ('min_activities', 'required_field', 'min_product_lines', 'min_amount')),
    activity_type   TEXT,
    min_count       INTEGER,
    field_name      TEXT,
    min_amount      INTEGER,
    only_forward    INTEGER NOT NULL DEFAULT 1,
    custom_message  TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_by      INTEGER REFERENCES users(id),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rules_stage ON stage_exit_rules(stage_id);

-- ======================= SCRUM-99: HOẠT ĐỘNG VỚI KHÁCH HÀNG =======================
CREATE TABLE IF NOT EXISTS activities (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type     TEXT NOT NULL CHECK (activity_type IN ('call', 'meeting', 'email', 'note')),
    status            TEXT NOT NULL CHECK (status IN ('completed', 'planned')),
    subject           TEXT,
    content           TEXT,
    outcome           TEXT,
    occurred_at       TEXT NOT NULL,
    duration_minutes  INTEGER CHECK (duration_minutes IS NULL OR duration_minutes BETWEEN 0 AND 1440),
    customer_id       INTEGER NOT NULL REFERENCES customers(id),
    contact_id        INTEGER REFERENCES contacts(id),
    opportunity_id    INTEGER REFERENCES opportunities(id),
    owner_id          INTEGER NOT NULL REFERENCES users(id),
    logged_via        TEXT NOT NULL DEFAULT 'web' CHECK (logged_via IN ('web', 'mobile')),
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activities_customer ON activities(customer_id);
CREATE INDEX IF NOT EXISTS idx_activities_opp ON activities(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_activities_owner ON activities(owner_id);
CREATE INDEX IF NOT EXISTS idx_activities_time ON activities(occurred_at);

-- ======================= SCRUM-100: CÔNG VIỆC CÓ HẠN =======================
CREATE TABLE IF NOT EXISTS tasks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT NOT NULL,
    description         TEXT,
    due_date            TEXT NOT NULL,
    priority            TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status              TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done')),
    assignee_id         INTEGER NOT NULL REFERENCES users(id),
    created_by          INTEGER NOT NULL REFERENCES users(id),
    customer_id         INTEGER REFERENCES customers(id),
    opportunity_id      INTEGER REFERENCES opportunities(id),
    postpone_count      INTEGER NOT NULL DEFAULT 0,
    completed_at        TEXT,
    completed_by        INTEGER REFERENCES users(id),
    completion_note     TEXT,
    source_activity_id  INTEGER REFERENCES activities(id),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    CHECK (customer_id IS NOT NULL OR opportunity_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);

CREATE TABLE IF NOT EXISTS task_postponements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id       INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    old_due_date  TEXT NOT NULL,
    new_due_date  TEXT NOT NULL,
    reason        TEXT NOT NULL,
    postponed_by  INTEGER NOT NULL REFERENCES users(id),
    postponed_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_postponements_task ON task_postponements(task_id);
