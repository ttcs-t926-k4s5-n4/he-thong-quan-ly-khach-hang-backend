-- =============================================================================
-- SCRUM-86: Danh sách Lead với Bộ lọc nâng cao + Bộ lọc lưu sẵn
-- Database: crm_db | SQL Server 2019+
-- (Bao gồm schema của SCRUM-84 vì SCRUM-86 phụ thuộc vào bảng leads)
-- =============================================================================

-- 1. Bảng Leads (từ SCRUM-84 — đảm bảo tồn tại)
IF OBJECT_ID(N'dbo.leads', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.leads (
        id                  INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        full_name           NVARCHAR(255)   NOT NULL,
        email               NVARCHAR(255)   NULL,
        phone               NVARCHAR(50)    NULL,
        company             NVARCHAR(255)   NULL,
        source              NVARCHAR(100)   NULL,
        classification      VARCHAR(10)     NOT NULL CONSTRAINT DF_leads_classification DEFAULT ('cold'),
        status              NVARCHAR(50)    NOT NULL CONSTRAINT DF_leads_status DEFAULT (N'Mới'),
        assigned_to         INT             NULL,
        assigned_at         BIGINT          NULL,
        sla_deadline_at     BIGINT          NULL,
        sla_breached        BIT             NOT NULL CONSTRAINT DF_leads_sla_breached DEFAULT (0),
        sla_alert_sent      BIT             NOT NULL CONSTRAINT DF_leads_sla_alert DEFAULT (0),
        rejection_reason    NVARCHAR(1000)  NULL,
        rejection_count     INT             NOT NULL CONSTRAINT DF_leads_rej_count DEFAULT (0),
        converted_at        BIGINT          NULL,
        customer_id         INT             NULL,
        notes               NVARCHAR(MAX)   NULL,
        created_by          INT             NOT NULL,
        created_at          BIGINT          NOT NULL,
        updated_at          BIGINT          NOT NULL,
        CONSTRAINT FK_leads_assigned_to FOREIGN KEY (assigned_to) REFERENCES dbo.users(id),
        CONSTRAINT FK_leads_created_by  FOREIGN KEY (created_by)  REFERENCES dbo.users(id)
    );
END;
GO

-- 2. Bảng Lịch sử Hoạt động Lead (từ SCRUM-84)
IF OBJECT_ID(N'dbo.lead_activities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lead_activities (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        lead_id         INT             NOT NULL,
        activity_type   NVARCHAR(100)   NOT NULL,
        description     NVARCHAR(MAX)   NULL,
        performed_by    INT             NULL,
        created_at      BIGINT          NOT NULL,
        CONSTRAINT FK_lead_activities_lead      FOREIGN KEY (lead_id)      REFERENCES dbo.leads(id),
        CONSTRAINT FK_lead_activities_performer FOREIGN KEY (performed_by) REFERENCES dbo.users(id)
    );
END;
GO

-- 3. Bảng Bộ lọc Lead đã lưu sẵn (MỚI - SCRUM-86)
IF OBJECT_ID(N'dbo.lead_saved_filters', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lead_saved_filters (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id         INT             NOT NULL,
            -- Chủ sở hữu bộ lọc (mỗi nhân viên có bộ lọc riêng)
        name            NVARCHAR(255)   NOT NULL,
            -- Tên gợi nhớ: "Leads nóng tuần này", "Cần gọi hôm nay"...
        criteria_json   NVARCHAR(MAX)   NOT NULL,
            -- JSON chứa: { status, source, classification, assigned_to, date_from, date_to, sla_breached_only, ... }
        created_at      BIGINT          NOT NULL,
        updated_at      BIGINT          NOT NULL,
        CONSTRAINT FK_lsf_user FOREIGN KEY (user_id) REFERENCES dbo.users(id)
    );
END;
GO

-- 4. Index tăng tốc truy vấn lead
CREATE INDEX IX_leads_classification ON dbo.leads (classification, status);
CREATE INDEX IX_leads_source         ON dbo.leads (source, status);
CREATE INDEX IX_leads_sla_deadline   ON dbo.leads (sla_deadline_at, status);
CREATE INDEX IX_lead_saved_filters   ON dbo.lead_saved_filters (user_id);
GO

-- =============================================================================
-- Cấu trúc criteria_json (ví dụ):
-- {
--   "q": "",
--   "status": "Đang chăm sóc",
--   "source": "Facebook",
--   "classification": "hot",
--   "assigned_to": 5,
--   "date_from": 1725196800000,
--   "date_to": 1727788800000,
--   "sla_breached_only": false,
--   "sort_by": "sla_deadline_at",
--   "order": "asc"
-- }
--
-- sla_status trong response:
-- - "ok"           → SLA còn hơn 8 giờ
-- - "warning"      → SLA còn dưới 8 giờ (frontend hiển thị màu vàng)
-- - "breached"     → Đã vượt SLA (frontend hiển thị màu đỏ, nổi bật)
-- - "not_assigned" → Chưa được phân công
-- =============================================================================
