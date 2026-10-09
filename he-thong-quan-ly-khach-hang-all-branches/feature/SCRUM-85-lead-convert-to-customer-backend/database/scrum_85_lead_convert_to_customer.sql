-- =============================================================================
-- SCRUM-85: Chuyển Lead thành Khách hàng, Người liên hệ và Cơ hội bán hàng
-- Database: crm_db | SQL Server 2019+
-- (Bao gồm cả schema của SCRUM-84 vì SCRUM-85 phụ thuộc vào bảng leads)
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

-- 3. Bảng Người liên hệ (Contact Person) của Khách hàng doanh nghiệp (MỚI - SCRUM-85)
IF OBJECT_ID(N'dbo.lead_contacts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lead_contacts (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customer_id     INT             NOT NULL,
            -- FK → dbo.customers.id (khách hàng doanh nghiệp vừa được tạo)
        lead_id         INT             NOT NULL,
            -- FK → dbo.leads.id (nguồn gốc lead)
        full_name       NVARCHAR(255)   NOT NULL,
        email           NVARCHAR(255)   NULL,
        phone           NVARCHAR(50)    NULL,
        position        NVARCHAR(255)   NULL,
            -- Chức vụ người liên hệ (VD: Giám đốc mua hàng, Kỹ thuật trưởng...)
        is_primary      BIT             NOT NULL CONSTRAINT DF_lc_primary DEFAULT (1),
            -- Người liên hệ chính (từ lead chuyển đổi luôn là primary)
        created_at      BIGINT          NOT NULL,
        CONSTRAINT FK_lead_contacts_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
        CONSTRAINT FK_lead_contacts_lead     FOREIGN KEY (lead_id)     REFERENCES dbo.leads(id)
    );
END;
GO

-- 4. Index
CREATE INDEX IX_lead_contacts_customer ON dbo.lead_contacts (customer_id);
CREATE INDEX IX_lead_contacts_lead     ON dbo.lead_contacts (lead_id);
GO

-- =============================================================================
-- Luồng chuyển đổi (SCRUM-85):
-- 1. POST /api/leads/{id}/convert
-- 2. Backend tạo đồng thời: dbo.customers + dbo.lead_contacts + dbo.opportunities
-- 3. UPDATE dbo.leads SET status = 'Đã chuyển đổi', customer_id = <new_id>
-- 4. Nhân bản dbo.lead_activities → dbo.customer_interactions
--    (để giữ lại toàn bộ lịch sử trên khách hàng mới)
-- 5. Lead bị khóa: mọi UPDATE sẽ raise ValueError("lead_already_converted")
-- =============================================================================
