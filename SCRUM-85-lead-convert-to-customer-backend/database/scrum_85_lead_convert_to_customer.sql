-- =============================================================================
-- SCRUM-85: Chuyß╗ân Lead th├ánh Kh├ích h├áng, Ng╞░ß╗¥i li├¬n hß╗ç v├á C╞í hß╗Öi b├ín h├áng
-- Database: crm_db | SQL Server 2019+
-- (Bao gß╗ôm cß║ú schema cß╗ºa SCRUM-84 v├¼ SCRUM-85 phß╗Ñ thuß╗Öc v├áo bß║úng leads)
-- =============================================================================

-- 1. Bß║úng Leads (tß╗½ SCRUM-84 ΓÇö ─æß║úm bß║úo tß╗ôn tß║íi)
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
        status              NVARCHAR(50)    NOT NULL CONSTRAINT DF_leads_status DEFAULT (N'Mß╗¢i'),
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

-- 2. Bß║úng Lß╗ïch sß╗¡ Hoß║ít ─æß╗Öng Lead (tß╗½ SCRUM-84)
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

-- 3. Bß║úng Ng╞░ß╗¥i li├¬n hß╗ç (Contact Person) cß╗ºa Kh├ích h├áng doanh nghiß╗çp (Mß╗ÜI - SCRUM-85)
IF OBJECT_ID(N'dbo.lead_contacts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lead_contacts (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customer_id     INT             NOT NULL,
            -- FK ΓåÆ dbo.customers.id (kh├ích h├áng doanh nghiß╗çp vß╗½a ─æ╞░ß╗úc tß║ío)
        lead_id         INT             NOT NULL,
            -- FK ΓåÆ dbo.leads.id (nguß╗ôn gß╗æc lead)
        full_name       NVARCHAR(255)   NOT NULL,
        email           NVARCHAR(255)   NULL,
        phone           NVARCHAR(50)    NULL,
        position        NVARCHAR(255)   NULL,
            -- Chß╗⌐c vß╗Ñ ng╞░ß╗¥i li├¬n hß╗ç (VD: Gi├ím ─æß╗æc mua h├áng, Kß╗╣ thuß║¡t tr╞░ß╗ƒng...)
        is_primary      BIT             NOT NULL CONSTRAINT DF_lc_primary DEFAULT (1),
            -- Ng╞░ß╗¥i li├¬n hß╗ç ch├¡nh (tß╗½ lead chuyß╗ân ─æß╗òi lu├┤n l├á primary)
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
-- Luß╗ông chuyß╗ân ─æß╗òi (SCRUM-85):
-- 1. POST /api/leads/{id}/convert
-- 2. Backend tß║ío ─æß╗ông thß╗¥i: dbo.customers + dbo.lead_contacts + dbo.opportunities
-- 3. UPDATE dbo.leads SET status = '─É├ú chuyß╗ân ─æß╗òi', customer_id = <new_id>
-- 4. Nh├ón bß║ún dbo.lead_activities ΓåÆ dbo.customer_interactions
--    (─æß╗â giß╗» lß║íi to├án bß╗Ö lß╗ïch sß╗¡ tr├¬n kh├ích h├áng mß╗¢i)
-- 5. Lead bß╗ï kh├│a: mß╗ìi UPDATE sß║╜ raise ValueError("lead_already_converted")
-- =============================================================================
