-- =============================================================================
-- SCRUM-76: Yêu cầu Hỗ trợ Sau bán & Gắn cờ Rủi ro Rời bỏ (Churn Risk)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Thêm cột cờ rủi ro rời bỏ vào dbo.customers (nếu chưa có)
IF NOT EXISTS (SELECT * FROM sys.columns
               WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'is_churn_risk')
BEGIN
    ALTER TABLE dbo.customers ADD is_churn_risk BIT NOT NULL DEFAULT 0;
END;
GO

IF NOT EXISTS (SELECT * FROM sys.columns
               WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'churn_risk_reason')
BEGIN
    ALTER TABLE dbo.customers ADD churn_risk_reason NVARCHAR(500) NULL;
END;
GO

IF NOT EXISTS (SELECT * FROM sys.columns
               WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'last_interaction_at')
BEGIN
    ALTER TABLE dbo.customers ADD last_interaction_at BIGINT NULL;
END;
GO

-- 2. Bảng Yêu cầu Hỗ trợ (Support Tickets)
IF OBJECT_ID(N'dbo.support_tickets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.support_tickets (
        id          INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ticket_code VARCHAR(50)   NOT NULL UNIQUE,
        customer_id INT           NOT NULL,
        title       NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX) NULL,
        priority    VARCHAR(20)   NOT NULL CONSTRAINT DF_st_priority DEFAULT ('medium'),
            -- Giá trị hợp lệ: 'low' | 'medium' | 'high' | 'urgent'
        status      VARCHAR(20)   NOT NULL CONSTRAINT DF_st_status DEFAULT ('open'),
            -- Giá trị hợp lệ: 'open' | 'in_progress' | 'resolved' | 'closed'
        assignee_id INT           NULL,
        created_by  INT           NOT NULL,
        created_at  BIGINT        NOT NULL CONSTRAINT DF_st_created DEFAULT (0),
        updated_at  BIGINT        NOT NULL CONSTRAINT DF_st_updated DEFAULT (0),
        CONSTRAINT FK_tickets_customer  FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
        CONSTRAINT FK_tickets_assignee  FOREIGN KEY (assignee_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_tickets_creator   FOREIGN KEY (created_by)  REFERENCES dbo.users(id)
    );
END;
GO

-- Index tăng tốc lọc theo customer_id và status
CREATE INDEX IF NOT EXISTS IX_tickets_customer_status
    ON dbo.support_tickets (customer_id, status);
GO
