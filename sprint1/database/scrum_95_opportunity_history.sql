-- ===========================================================================
-- SCRUM-95: Lịch sử thay đổi cơ hội kinh doanh (Opportunity Change History)
-- Theo dõi thay đổi: Stage, Value, Expected Close Date, Owner
-- Hệ quản trị CSDL: Microsoft SQL Server
-- ===========================================================================

-- 1. Bổ sung cột owner_id vào dbo.opportunities (nếu chưa có)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'owner_id'
)
BEGIN
    ALTER TABLE dbo.opportunities ADD owner_id INT NULL;
    PRINT N'Added column owner_id to dbo.opportunities';
END;
GO

-- Cập nhật dữ liệu cũ nếu owner_id đang NULL -> lấy từ created_by
UPDATE dbo.opportunities
SET owner_id = created_by
WHERE owner_id IS NULL;
GO

-- 2. Tạo bảng dbo.opportunity_history
IF OBJECT_ID(N'dbo.opportunity_history', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunity_history (
        id              BIGINT          IDENTITY(1,1) NOT NULL PRIMARY KEY,
        opportunity_id  INT             NOT NULL,
        field_name      NVARCHAR(100)   NOT NULL,
        old_value       NVARCHAR(MAX)   NULL,
        new_value       NVARCHAR(MAX)   NULL,
        changed_by      INT             NOT NULL,
        changed_at      BIGINT          NOT NULL,
        CONSTRAINT FK_opp_hist_opportunity 
            FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
        CONSTRAINT FK_opp_hist_user 
            FOREIGN KEY (changed_by) REFERENCES dbo.users(id)
    );
    PRINT N'Created table dbo.opportunity_history';
END;
GO

-- 3. Tạo Indexes tối ưu hóa truy vấn lịch sử theo cơ hội và thời gian
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_history') AND name = N'IX_opp_hist_opp_id_changed_at'
)
BEGIN
    CREATE INDEX IX_opp_hist_opp_id_changed_at 
    ON dbo.opportunity_history (opportunity_id, changed_at DESC);
    PRINT N'Created index IX_opp_hist_opp_id_changed_at';
END;
GO

-- 4. Tạo Indexes lọc theo trường thay đổi
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_history') AND name = N'IX_opp_hist_field_name'
)
BEGIN
    CREATE INDEX IX_opp_hist_field_name 
    ON dbo.opportunity_history (opportunity_id, field_name);
    PRINT N'Created index IX_opp_hist_field_name';
END;
GO
