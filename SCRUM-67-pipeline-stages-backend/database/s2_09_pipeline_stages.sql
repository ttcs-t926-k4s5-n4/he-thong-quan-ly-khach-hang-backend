-- =============================================================================
-- S2-09: Cß║Ñu h├¼nh c├íc giai ─æoß║ín Pipeline & X├íc suß║Ñt thß║»ng (Sales Manager)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

IF OBJECT_ID(N'dbo.pipeline_stages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.pipeline_stages (
        id                       INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        stage_key                NVARCHAR(50)  NOT NULL UNIQUE,
        stage_name               NVARCHAR(150) NOT NULL,
        win_probability          INT           NOT NULL CONSTRAINT DF_ps_win_prob DEFAULT (0),
        display_order            INT           NOT NULL CONSTRAINT DF_ps_order DEFAULT (0),
        required_conditions_json NVARCHAR(MAX) NULL, -- JSON ─æiß╗üu kiß╗çn bß║»t buß╗Öc (vd: {"min_meetings": 1})
        is_won_stage             BIT           NOT NULL CONSTRAINT DF_ps_is_won DEFAULT (0),
        is_lost_stage            BIT           NOT NULL CONSTRAINT DF_ps_is_lost DEFAULT (0),
        is_active                BIT           NOT NULL CONSTRAINT DF_ps_is_active DEFAULT (1),
        created_at               BIGINT        NOT NULL CONSTRAINT DF_ps_created DEFAULT (0),
        updated_at               BIGINT        NOT NULL CONSTRAINT DF_ps_updated DEFAULT (0)
    );
END;
GO
