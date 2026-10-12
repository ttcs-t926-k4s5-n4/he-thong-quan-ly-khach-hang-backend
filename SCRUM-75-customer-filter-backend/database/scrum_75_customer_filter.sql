-- =============================================================================
-- SCRUM-75: Bß╗Ö lß╗ìc n├óng cao & Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u cho Kh├ích h├áng
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Bß║úng l╞░u trß╗» bß╗Ö lß╗ìc ─æ├ú l╞░u cß╗ºa tß╗½ng ng╞░ß╗¥i d├╣ng
IF OBJECT_ID(N'dbo.saved_filters', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.saved_filters (
        id            INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id       INT           NOT NULL,
        name          NVARCHAR(255) NOT NULL,
        filter_target VARCHAR(50)   NOT NULL CONSTRAINT DF_sf_target DEFAULT ('customer'),
        criteria_json NVARCHAR(MAX) NOT NULL,
        created_at    BIGINT        NOT NULL CONSTRAINT DF_sf_created DEFAULT (0),
        updated_at    BIGINT        NOT NULL CONSTRAINT DF_sf_updated DEFAULT (0),
        CONSTRAINT FK_saved_filters_user FOREIGN KEY (user_id) REFERENCES dbo.users(id)
    );
END;
GO

-- Mß║½u dß╗» liß╗çu seed (tuß╗│ chß╗ìn)
-- INSERT INTO dbo.saved_filters (user_id, name, filter_target, criteria_json, created_at, updated_at)
-- VALUES (1, N'Kh├ích h├áng VIP ΓÇô HN', 'customer',
--         N'{"status":"Tiß╗üm n─âng","region":"H├á Nß╗Öi","industry":"C├┤ng nghß╗ç"}',
--         DATEDIFF(MILLISECOND,'1970-01-01',GETUTCDATE()),
--         DATEDIFF(MILLISECOND,'1970-01-01',GETUTCDATE()));
GO
