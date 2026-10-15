-- =============================================================================
-- SCRUM-84: Nhß║¡n/Tß╗½ chß╗æi Lead vß╗¢i r├áng buß╗Öc SLA phß║ún hß╗ôi
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Bß║úng Leads (quß║ún l├╜ v├▓ng ─æß╗¥i lead tß╗½ khi tß║ío ─æß║┐n khi chuyß╗ân ─æß╗òi)
IF OBJECT_ID(N'dbo.leads', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.leads (
        id                  INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        full_name           NVARCHAR(255)   NOT NULL,
        email               NVARCHAR(255)   NULL,
        phone               NVARCHAR(50)    NULL,
        company             NVARCHAR(255)   NULL,
        source              NVARCHAR(100)   NULL,
        classification      VARCHAR(10)     NOT NULL
            CONSTRAINT DF_leads_classification DEFAULT ('cold'),
            -- 'hot' = N├│ng | 'warm' = ß║ñm | 'cold' = Lß║ính
        status              NVARCHAR(50)    NOT NULL
            CONSTRAINT DF_leads_status DEFAULT (N'Mß╗¢i'),
            -- Mß╗¢i | ─É├ú ph├ón c├┤ng | ─Éang ch─âm s├│c | Chß╗¥ ph├ón bß╗ò | ─É├ú chuyß╗ân ─æß╗òi | ─É├ú tß╗½ chß╗æi
        assigned_to         INT             NULL,
        assigned_at         BIGINT          NULL,
        sla_deadline_at     BIGINT          NULL,
            -- assigned_at + 3 ng├áy (ms)
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

-- 2. Bß║úng Lß╗ïch sß╗¡ Hoß║ít ─æß╗Öng Lead
IF OBJECT_ID(N'dbo.lead_activities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lead_activities (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        lead_id         INT             NOT NULL,
        activity_type   NVARCHAR(100)   NOT NULL,
            -- 'created' | 'assigned' | 'accepted' | 'rejected' | 'sla_breached' | 'converted' | 'note' | 'updated'
        description     NVARCHAR(MAX)   NULL,
        performed_by    INT             NULL,
        created_at      BIGINT          NOT NULL,
        CONSTRAINT FK_lead_activities_lead      FOREIGN KEY (lead_id)      REFERENCES dbo.leads(id),
        CONSTRAINT FK_lead_activities_performer FOREIGN KEY (performed_by) REFERENCES dbo.users(id)
    );
END;
GO

-- 3. Index hß╗ù trß╗ú truy vß║Ñn hiß╗çu suß║Ñt cao
CREATE INDEX IX_leads_assigned_to     ON dbo.leads (assigned_to, status);
CREATE INDEX IX_leads_sla_deadline    ON dbo.leads (sla_deadline_at, status);
CREATE INDEX IX_leads_status          ON dbo.leads (status, created_at DESC);
CREATE INDEX IX_lead_activities_lead  ON dbo.lead_activities (lead_id, created_at DESC);
GO

-- =============================================================================
-- Ghi ch├║ thiß║┐t kß║┐ SLA:
-- - SLA bß║»t ─æß║ºu t├¡nh khi assigned_at ─æ╞░ß╗úc ghi (l├║c ph├ón c├┤ng).
-- - sla_deadline_at = assigned_at + 3 * 86400000 (3 ng├áy t├¡nh bß║▒ng ms).
-- - sla_breached = 1 khi NOW() > sla_deadline_at m├á trß║íng th├íi vß║½n = '─É├ú ph├ón c├┤ng'.
-- - check_and_flag_sla_breached_leads() n├¬n ─æ╞░ß╗úc gß╗ìi ─æß╗ïnh kß╗│ (scheduler).
-- =============================================================================
