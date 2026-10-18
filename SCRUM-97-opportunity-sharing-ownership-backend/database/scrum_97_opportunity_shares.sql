-- ===========================================================================
-- SCRUM-97: Chia sẻ cơ hội kinh doanh & Chuyển quyền sở hữu (Opportunity Sharing & Ownership)
-- Hệ quản trị CSDL: Microsoft SQL Server
-- ===========================================================================

-- 1. Tạo bảng dbo.opportunity_shares
IF OBJECT_ID(N'dbo.opportunity_shares', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunity_shares (
        id                  BIGINT          IDENTITY(1,1) NOT NULL PRIMARY KEY,
        opportunity_id      INT             NOT NULL,
        user_id             INT             NOT NULL,
        shared_by           INT             NOT NULL,
        permission_level    NVARCHAR(50)    NOT NULL CONSTRAINT DF_opp_share_perm DEFAULT ('read'),
        created_at          BIGINT          NOT NULL,
        updated_at          BIGINT          NOT NULL,
        CONSTRAINT FK_opp_share_opportunity 
            FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
        CONSTRAINT FK_opp_share_user 
            FOREIGN KEY (user_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_opp_share_shared_by 
            FOREIGN KEY (shared_by) REFERENCES dbo.users(id),
        CONSTRAINT UQ_opp_share_user 
            UNIQUE (opportunity_id, user_id)
    );
    PRINT N'Created table dbo.opportunity_shares';
END;
GO

-- 2. Tạo Indexes tối ưu hóa truy vấn chia sẻ
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_shares') AND name = N'IX_opp_shares_opp_id'
)
BEGIN
    CREATE INDEX IX_opp_shares_opp_id ON dbo.opportunity_shares (opportunity_id);
    PRINT N'Created index IX_opp_shares_opp_id';
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_shares') AND name = N'IX_opp_shares_user_id'
)
BEGIN
    CREATE INDEX IX_opp_shares_user_id ON dbo.opportunity_shares (user_id);
    PRINT N'Created index IX_opp_shares_user_id';
END;
GO
