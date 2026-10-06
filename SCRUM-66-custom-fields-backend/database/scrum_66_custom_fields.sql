-- =============================================================================
-- SCRUM-17 / SCRUM-66: Khai b├ío tr╞░ß╗¥ng t├╣y chß╗ënh cho Kh├ích h├áng & C╞í hß╗Öi
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. dbo.custom_field_definitions ΓÇö Quß║ún l├╜ ─æß╗ïnh ngh─⌐a tr╞░ß╗¥ng t├╣y chß╗ënh
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.custom_field_definitions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.custom_field_definitions (
        id            INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        entity_type   NVARCHAR(50)  NOT NULL, -- 'customer' hoß║╖c 'opportunity'
        field_key     NVARCHAR(100) NOT NULL, -- m├ú duy nhß║Ñt (vd: facebook_url, budget_usd, contract_date, industry)
        field_label   NVARCHAR(200) NOT NULL, -- nh├ún hiß╗ân thß╗ï (vd: Link Facebook, Ng├ón s├ích USD, Ng├ánh nghß╗ü)
        field_type    NVARCHAR(50)  NOT NULL, -- 'text', 'number', 'date', 'select'
        options       NVARCHAR(MAX) NULL,     -- Danh s├ích t├╣y chß╗ìn dß║íng JSON (d├╣ng cho 'select', vd: ["Doanh nghiß╗çp", "C├í nh├ón"])
        is_required   BIT           NOT NULL CONSTRAINT DF_cfd_is_required DEFAULT (0),
        description   NVARCHAR(500) NULL,     -- M├┤ tß║ú hoß║╖c gß╗úi ├╜ nhß║¡p liß╗çu
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
-- 2. dbo.customers ΓÇö Danh mß╗Ñc Kh├ích h├áng
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers (
        id          INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name        NVARCHAR(200) NOT NULL,
        phone       NVARCHAR(50)  NULL,
        email       NVARCHAR(255) NULL,
        address     NVARCHAR(500) NULL,
        status      NVARCHAR(50)  NOT NULL CONSTRAINT DF_customers_status DEFAULT (N'Mß╗¢i'),
        created_by  INT           NOT NULL,
        created_at  BIGINT        NOT NULL CONSTRAINT DF_customers_created DEFAULT (0),
        updated_at  BIGINT        NOT NULL CONSTRAINT DF_customers_updated DEFAULT (0)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 3. dbo.opportunities ΓÇö Danh mß╗Ñc C╞í hß╗Öi kinh doanh
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.opportunities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunities (
        id                  INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        title               NVARCHAR(250)  NOT NULL,
        customer_id         INT            NOT NULL,
        value               DECIMAL(18,2)  NOT NULL CONSTRAINT DF_opp_value DEFAULT (0),
        stage               NVARCHAR(100)  NOT NULL CONSTRAINT DF_opp_stage DEFAULT (N'Mß╗¢i tß║ío'),
        expected_close_date NVARCHAR(20)   NULL,
        created_by          INT            NOT NULL,
        created_at          BIGINT         NOT NULL CONSTRAINT DF_opp_created DEFAULT (0),
        updated_at          BIGINT         NOT NULL CONSTRAINT DF_opp_updated DEFAULT (0),
        CONSTRAINT FK_opportunities_customers FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE
    );
END;
GO

-- ---------------------------------------------------------------------------
-- 4. dbo.custom_field_values ΓÇö L╞░u trß╗» gi├í trß╗ï tr╞░ß╗¥ng t├╣y chß╗ënh cß╗ºa ─æß╗æi t╞░ß╗úng
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.custom_field_values', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.custom_field_values (
        id          BIGINT        IDENTITY(1,1) NOT NULL PRIMARY KEY,
        entity_type NVARCHAR(50)  NOT NULL, -- 'customer' hoß║╖c 'opportunity'
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
