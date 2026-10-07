-- =============================================================================
-- SCRUM-77: Chăm sóc Khách hàng Định kỳ & Lịch sử Tương tác
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Thêm cột last_interaction_at vào dbo.customers (nếu chưa có)
IF NOT EXISTS (SELECT * FROM sys.columns
               WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'last_interaction_at')
BEGIN
    ALTER TABLE dbo.customers ADD last_interaction_at BIGINT NULL;
END;
GO

-- 2. Bảng Lịch sử Tương tác Chăm sóc Khách hàng
IF OBJECT_ID(N'dbo.customer_interactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_interactions (
        id               INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customer_id      INT            NOT NULL,
        interaction_type NVARCHAR(50)   NOT NULL
            CONSTRAINT DF_ci_type DEFAULT (N'Gọi điện chăm sóc'),
            -- Ví dụ: 'Gọi điện chăm sóc' | 'Gửi email' | 'Gặp trực tiếp' | 'Đánh dấu đã liên hệ ngay'
        notes            NVARCHAR(MAX)  NULL,
        created_by       INT            NOT NULL,
        created_at       BIGINT         NOT NULL CONSTRAINT DF_ci_created DEFAULT (0),
        CONSTRAINT FK_interactions_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
        CONSTRAINT FK_interactions_creator  FOREIGN KEY (created_by)  REFERENCES dbo.users(id)
    );
END;
GO

-- Index tăng tốc truy vấn danh sách tương tác theo khách hàng
CREATE INDEX IF NOT EXISTS IX_interactions_customer
    ON dbo.customer_interactions (customer_id, created_at DESC);
GO

-- Ghi chú quan trọng:
-- Cột last_interaction_at trong dbo.customers được tự động cập nhật mỗi khi
-- record_customer_interaction() được gọi từ periodic_care.py.
-- Logic lọc "chưa tương tác trong N ngày" sử dụng:
--   WHERE ISNULL(c.last_interaction_at, c.created_at) <= (now_ms - N * 86400000)
GO
