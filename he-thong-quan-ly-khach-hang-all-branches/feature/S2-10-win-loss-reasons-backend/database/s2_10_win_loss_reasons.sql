-- =============================================================================
-- S2-10: Khai báo Danh mục Lý do Thắng/Thua & Đối thủ cạnh tranh (Sales Manager)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. dbo.win_loss_reasons — Lý do Thắng / Thua
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
-- 2. dbo.competitors — Đối thủ cạnh tranh
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
