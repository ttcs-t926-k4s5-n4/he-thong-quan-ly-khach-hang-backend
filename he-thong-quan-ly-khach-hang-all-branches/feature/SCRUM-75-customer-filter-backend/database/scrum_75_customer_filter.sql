-- =============================================================================
-- SCRUM-75: Bộ lọc nâng cao & Quản lý Bộ lọc đã lưu cho Khách hàng
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Bảng lưu trữ bộ lọc đã lưu của từng người dùng
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

-- Mẫu dữ liệu seed (tuỳ chọn)
-- INSERT INTO dbo.saved_filters (user_id, name, filter_target, criteria_json, created_at, updated_at)
-- VALUES (1, N'Khách hàng VIP – HN', 'customer',
--         N'{"status":"Tiềm năng","region":"Hà Nội","industry":"Công nghệ"}',
--         DATEDIFF(MILLISECOND,'1970-01-01',GETUTCDATE()),
--         DATEDIFF(MILLISECOND,'1970-01-01',GETUTCDATE()));
GO
