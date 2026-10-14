-- =============================================================================
-- SCRUM-77: Ch─âm s├│c Kh├ích h├áng ─Éß╗ïnh kß╗│ & Lß╗ïch sß╗¡ T╞░╞íng t├íc
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Th├¬m cß╗Öt last_interaction_at v├áo dbo.customers (nß║┐u ch╞░a c├│)
IF NOT EXISTS (SELECT * FROM sys.columns
               WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'last_interaction_at')
BEGIN
    ALTER TABLE dbo.customers ADD last_interaction_at BIGINT NULL;
END;
GO

-- 2. Bß║úng Lß╗ïch sß╗¡ T╞░╞íng t├íc Ch─âm s├│c Kh├ích h├áng
IF OBJECT_ID(N'dbo.customer_interactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_interactions (
        id               INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customer_id      INT            NOT NULL,
        interaction_type NVARCHAR(50)   NOT NULL
            CONSTRAINT DF_ci_type DEFAULT (N'Gß╗ìi ─æiß╗çn ch─âm s├│c'),
            -- V├¡ dß╗Ñ: 'Gß╗ìi ─æiß╗çn ch─âm s├│c' | 'Gß╗¡i email' | 'Gß║╖p trß╗▒c tiß║┐p' | '─É├ính dß║Ñu ─æ├ú li├¬n hß╗ç ngay'
        notes            NVARCHAR(MAX)  NULL,
        created_by       INT            NOT NULL,
        created_at       BIGINT         NOT NULL CONSTRAINT DF_ci_created DEFAULT (0),
        CONSTRAINT FK_interactions_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
        CONSTRAINT FK_interactions_creator  FOREIGN KEY (created_by)  REFERENCES dbo.users(id)
    );
END;
GO

-- Index t─âng tß╗æc truy vß║Ñn danh s├ích t╞░╞íng t├íc theo kh├ích h├áng
CREATE INDEX IF NOT EXISTS IX_interactions_customer
    ON dbo.customer_interactions (customer_id, created_at DESC);
GO

-- Ghi ch├║ quan trß╗ìng:
-- Cß╗Öt last_interaction_at trong dbo.customers ─æ╞░ß╗úc tß╗▒ ─æß╗Öng cß║¡p nhß║¡t mß╗ùi khi
-- record_customer_interaction() ─æ╞░ß╗úc gß╗ìi tß╗½ periodic_care.py.
-- Logic lß╗ìc "ch╞░a t╞░╞íng t├íc trong N ng├áy" sß╗¡ dß╗Ñng:
--   WHERE ISNULL(c.last_interaction_at, c.created_at) <= (now_ms - N * 86400000)
GO
