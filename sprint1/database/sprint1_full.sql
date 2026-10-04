-- =============================================================================
-- Sprint 1 — Schema tổng hợp
-- Database: crm_db  |  SQL Server 2019+
-- Chạy file này một lần để tạo toàn bộ bảng cần thiết cho Sprint 1
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. dbo.users — Tài khoản người dùng (S1-01, S1-02, S1-04, S1-05, S1-08)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id                   INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        full_name            NVARCHAR(150)  NOT NULL,
        email                NVARCHAR(255)  NOT NULL,
        password_hash        NVARCHAR(512)  NOT NULL,
        -- Vai trò đơn giản (admin / manager / employee) dùng cho S1-01..S1-06
        role                 NVARCHAR(50)   NOT NULL CONSTRAINT DF_users_role DEFAULT (N'employee'),
        -- Trường mở rộng cho S1-08 (quản lý tài khoản)
        group_name           NVARCHAR(120)  NOT NULL CONSTRAINT DF_users_group DEFAULT (N''),
        role_name            NVARCHAR(120)  NOT NULL CONSTRAINT DF_users_role_name DEFAULT (N'Nhân viên kinh doanh'),
        status               NVARCHAR(50)   NOT NULL CONSTRAINT DF_users_status DEFAULT (N'Chờ kích hoạt'),
        -- Chống brute-force (S1-01, S1-10)
        failed_login_attempts INT           NOT NULL CONSTRAINT DF_users_failures DEFAULT (0),
        locked_until         BIGINT         NULL,
        -- Đổi mật khẩu (S1-04): tăng version để vô hiệu phiên cũ
        credentials_version  INT            NOT NULL CONSTRAINT DF_users_cv DEFAULT (1),
        -- Bàn giao tài khoản (S1-10)
        is_active            BIT            NOT NULL CONSTRAINT DF_users_active DEFAULT (1),
        created_at           BIGINT         NOT NULL CONSTRAINT DF_users_created DEFAULT (0),
        updated_at           BIGINT         NOT NULL CONSTRAINT DF_users_updated DEFAULT (0)
    );
END;
GO

-- Unique email
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.users') AND name = N'UX_users_email'
)
    CREATE UNIQUE INDEX UX_users_email ON dbo.users(email);
GO

-- ---------------------------------------------------------------------------
-- 2. dbo.login_sessions — Phiên đăng nhập (S1-02, S1-04)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.login_sessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.login_sessions (
        id                  BIGINT   IDENTITY(1,1) NOT NULL PRIMARY KEY,
        token_hash          CHAR(64) NOT NULL UNIQUE,
        user_id             INT      NOT NULL,
        credentials_version INT      NOT NULL CONSTRAINT DF_ls_cv DEFAULT (1),
        created_at          BIGINT   NOT NULL,
        last_seen_at        BIGINT   NOT NULL,
        expires_at          BIGINT   NOT NULL,
        revoked_at          BIGINT   NULL,
        CONSTRAINT FK_login_sessions_users
            FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.login_sessions') AND name = N'IX_login_sessions_user'
)
    CREATE INDEX IX_login_sessions_user ON dbo.login_sessions(user_id);
GO

-- ---------------------------------------------------------------------------
-- 3. dbo.password_reset_tokens — Reset mật khẩu qua email (S1-03)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.password_reset_tokens', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.password_reset_tokens (
        id          BIGINT   IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id     INT      NOT NULL,
        token_hash  CHAR(64) NOT NULL UNIQUE,
        expires_at  BIGINT   NOT NULL,
        used_at     BIGINT   NULL,
        created_at  BIGINT   NOT NULL,
        CONSTRAINT FK_password_reset_tokens_users
            FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.password_reset_tokens') AND name = N'IX_prt_user'
)
    CREATE INDEX IX_prt_user ON dbo.password_reset_tokens(user_id);
GO

-- ---------------------------------------------------------------------------
-- 4. dbo.account_activation_tokens — Kích hoạt tài khoản mới (S1-08)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.account_activation_tokens', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.account_activation_tokens (
        id          BIGINT   IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id     INT      NOT NULL,
        token_hash  CHAR(64) NOT NULL UNIQUE,
        expires_at  BIGINT   NOT NULL,
        used_at     BIGINT   NULL,
        created_at  BIGINT   NOT NULL,
        CONSTRAINT FK_account_activation_tokens_users
            FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.account_activation_tokens') AND name = N'IX_aat_user'
)
    CREATE INDEX IX_aat_user ON dbo.account_activation_tokens(user_id);
GO

-- ---------------------------------------------------------------------------
-- 5. dbo.custom_field_definitions — Quản lý định nghĩa trường tùy chỉnh (SCRUM-66)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.custom_field_definitions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.custom_field_definitions (
        id            INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        entity_type   NVARCHAR(50)  NOT NULL, -- 'customer' hoặc 'opportunity'
        field_key     NVARCHAR(100) NOT NULL, -- mã duy nhất (vd: facebook_url, budget_usd, contract_date, industry)
        field_label   NVARCHAR(200) NOT NULL, -- nhãn hiển thị (vd: Link Facebook, Ngân sách USD)
        field_type    NVARCHAR(50)  NOT NULL, -- 'text', 'number', 'date', 'select'
        options       NVARCHAR(MAX) NULL,     -- Tùy chọn JSON cho 'select'
        is_required   BIT           NOT NULL CONSTRAINT DF_cfd_is_required DEFAULT (0),
        description   NVARCHAR(500) NULL,     -- Gợi ý nhập liệu
        display_order INT           NOT NULL CONSTRAINT DF_cfd_display_order DEFAULT (0),
        is_active     BIT           NOT NULL CONSTRAINT DF_cfd_is_active DEFAULT (1),
        created_at    BIGINT        NOT NULL CONSTRAINT DF_cfd_created_at DEFAULT (0),
        updated_at    BIGINT        NOT NULL CONSTRAINT DF_cfd_updated_at DEFAULT (0)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.custom_field_definitions') AND name = N'UX_cfd_entity_key'
)
    CREATE UNIQUE INDEX UX_cfd_entity_key ON dbo.custom_field_definitions(entity_type, field_key);
GO

-- ---------------------------------------------------------------------------
-- 6. dbo.customers — Khách hàng (SCRUM-66)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers (
        id          INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name        NVARCHAR(200) NOT NULL,
        phone       NVARCHAR(50)  NULL,
        email       NVARCHAR(255) NULL,
        address     NVARCHAR(500) NULL,
        status      NVARCHAR(50)  NOT NULL CONSTRAINT DF_customers_status DEFAULT (N'Mới'),
        created_by  INT           NOT NULL,
        created_at  BIGINT        NOT NULL CONSTRAINT DF_customers_created DEFAULT (0),
        updated_at  BIGINT        NOT NULL CONSTRAINT DF_customers_updated DEFAULT (0)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 7. dbo.opportunities — Cơ hội (SCRUM-66)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.opportunities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunities (
        id                  INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        title               NVARCHAR(250)  NOT NULL,
        customer_id         INT            NOT NULL,
        value               DECIMAL(18,2)  NOT NULL CONSTRAINT DF_opp_value DEFAULT (0),
        stage               NVARCHAR(100)  NOT NULL CONSTRAINT DF_opp_stage DEFAULT (N'Mới tạo'),
        expected_close_date NVARCHAR(20)   NULL,
        created_by          INT            NOT NULL,
        created_at          BIGINT         NOT NULL CONSTRAINT DF_opp_created DEFAULT (0),
        updated_at          BIGINT         NOT NULL CONSTRAINT DF_opp_updated DEFAULT (0),
        CONSTRAINT FK_opportunities_customers FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 8. dbo.custom_field_values — Giá trị trường tùy chỉnh (SCRUM-66)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.custom_field_values', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.custom_field_values (
        id          BIGINT        IDENTITY(1,1) NOT NULL PRIMARY KEY,
        entity_type NVARCHAR(50)  NOT NULL, -- 'customer' hoặc 'opportunity'
        entity_id   INT           NOT NULL,
        field_id    INT           NOT NULL,
        field_value NVARCHAR(MAX) NULL,
        created_at  BIGINT        NOT NULL CONSTRAINT DF_cfv_created DEFAULT (0),
        updated_at  BIGINT        NOT NULL CONSTRAINT DF_cfv_updated DEFAULT (0),
        CONSTRAINT FK_cfv_definitions FOREIGN KEY (field_id) REFERENCES dbo.custom_field_definitions(id) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.custom_field_values') AND name = N'UX_cfv_entity_field'
)
    CREATE UNIQUE INDEX UX_cfv_entity_field ON dbo.custom_field_values(entity_type, entity_id, field_id);
GO

-- ---------------------------------------------------------------------------
-- 9. dbo.pipeline_stages — Giai đoạn Pipeline & Xác suất thắng (S2-09)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.pipeline_stages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.pipeline_stages (
        id                       INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        stage_key                NVARCHAR(50)  NOT NULL UNIQUE,
        stage_name               NVARCHAR(150) NOT NULL,
        win_probability          INT           NOT NULL CONSTRAINT DF_ps_win_prob DEFAULT (0),
        display_order            INT           NOT NULL CONSTRAINT DF_ps_order DEFAULT (0),
        required_conditions_json NVARCHAR(MAX) NULL,
        is_won_stage             BIT           NOT NULL CONSTRAINT DF_ps_is_won DEFAULT (0),
        is_lost_stage            BIT           NOT NULL CONSTRAINT DF_ps_is_lost DEFAULT (0),
        is_active                BIT           NOT NULL CONSTRAINT DF_ps_is_active DEFAULT (1),
        created_at               BIGINT        NOT NULL CONSTRAINT DF_ps_created DEFAULT (0),
        updated_at               BIGINT        NOT NULL CONSTRAINT DF_ps_updated DEFAULT (0)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 10. dbo.win_loss_reasons — Danh mục Lý do Thắng/Thua (S2-10)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.win_loss_reasons', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.win_loss_reasons (
        id            INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        reason_type   NVARCHAR(20)  NOT NULL, -- 'win' hoặc 'loss'
        reason_code   NVARCHAR(50)  NOT NULL,
        reason_title  NVARCHAR(200) NOT NULL,
        description   NVARCHAR(500) NULL,
        is_active     BIT           NOT NULL CONSTRAINT DF_wlr_is_active DEFAULT (1),
        created_at    BIGINT        NOT NULL CONSTRAINT DF_wlr_created DEFAULT (0),
        updated_at    BIGINT        NOT NULL CONSTRAINT DF_wlr_updated DEFAULT (0),
        CONSTRAINT UX_wlr_type_code UNIQUE (reason_type, reason_code)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 11. dbo.competitors — Danh mục Đối thủ cạnh tranh (S2-10)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.competitors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.competitors (
        id         INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        code       NVARCHAR(50)  NOT NULL UNIQUE,
        name       NVARCHAR(200) NOT NULL,
        website    NVARCHAR(255) NULL,
        strengths  NVARCHAR(500) NULL,
        weaknesses NVARCHAR(500) NULL,
        is_active  BIT           NOT NULL CONSTRAINT DF_comp_is_active DEFAULT (1),
        created_at BIGINT        NOT NULL CONSTRAINT DF_comp_created DEFAULT (0),
        updated_at BIGINT        NOT NULL CONSTRAINT DF_comp_updated DEFAULT (0)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 12. Bổ sung các cột thông tin đóng cơ hội vào dbo.opportunities (S2-09, S2-10)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'stage_key')
    ALTER TABLE dbo.opportunities ADD stage_key NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'win_probability')
    ALTER TABLE dbo.opportunities ADD win_probability INT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'win_reason_id')
    ALTER TABLE dbo.opportunities ADD win_reason_id INT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'loss_reason_id')
    ALTER TABLE dbo.opportunities ADD loss_reason_id INT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'competitor_id')
    ALTER TABLE dbo.opportunities ADD competitor_id INT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'meetings_count')
    ALTER TABLE dbo.opportunities ADD meetings_count INT NOT NULL CONSTRAINT DF_opp_meetings DEFAULT (0);

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'closed_at')
    ALTER TABLE dbo.opportunities ADD closed_at BIGINT NULL;
GO

-- ---------------------------------------------------------------------------
-- 13. Hoàn tất — Dữ liệu mẫu được tạo bởi seed_data.py
-- ---------------------------------------------------------------------------
PRINT 'Sprint 1 & Sprint 2 (S2-09, S2-10, SCRUM-66) schema created successfully!';
GO


