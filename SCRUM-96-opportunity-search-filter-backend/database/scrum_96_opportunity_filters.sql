-- ===========================================================================
-- SCRUM-96: T├¼m kiß║┐m, lß╗ìc v├á l╞░u bß╗Ö lß╗ìc c╞í hß╗Öi kinh doanh (Saved Opportunity Filters)
-- Hß╗ç quß║ún trß╗ï CSDL: Microsoft SQL Server
-- ===========================================================================

-- 1. Bß╗ò sung cß╗Öt product_id v├áo dbo.opportunities (nß║┐u ch╞░a c├│)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'product_id'
)
BEGIN
    ALTER TABLE dbo.opportunities ADD product_id INT NULL;
    PRINT N'Added column product_id to dbo.opportunities';
END;
GO

-- 2. Tß║ío bß║úng dbo.saved_opportunity_filters l╞░u cß║Ñu h├¼nh bß╗Ö lß╗ìc ng╞░ß╗¥i d├╣ng
IF OBJECT_ID(N'dbo.saved_opportunity_filters', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.saved_opportunity_filters (
        id              INT             IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id         INT             NOT NULL,
        filter_name     NVARCHAR(255)   NOT NULL,
        filter_config   NVARCHAR(MAX)   NOT NULL,
        created_at      BIGINT          NOT NULL,
        updated_at      BIGINT          NOT NULL,
        CONSTRAINT FK_saved_opp_filters_user 
            FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
    PRINT N'Created table dbo.saved_opportunity_filters';
END;
GO

-- 3. Tß║ío Index cho user_id v├á thß╗¥i gian tß║ío
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dbo.saved_opportunity_filters') AND name = N'IX_saved_opp_filters_user_id'
)
BEGIN
    CREATE INDEX IX_saved_opp_filters_user_id 
    ON dbo.saved_opportunity_filters (user_id, created_at DESC);
    PRINT N'Created index IX_saved_opp_filters_user_id';
END;
GO
