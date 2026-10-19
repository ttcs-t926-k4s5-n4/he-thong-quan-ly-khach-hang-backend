-- =============================================================================
-- Migration: SCRUM-104 — Ghi nhanh kết quả cuộc gọi (Call Logs & Mobile Quick Record)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

IF OBJECT_ID(N'dbo.call_logs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.call_logs (
        id                BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customer_id       INT            NOT NULL,
        opportunity_id    INT            NULL,
        user_id           INT            NOT NULL,
        call_result       NVARCHAR(100)  NOT NULL,
        notes             NVARCHAR(1000) NULL,
        called_at         BIGINT         NOT NULL,
        callback_at       BIGINT         NULL,
        callback_task_id  INT            NULL,
        created_at        BIGINT         NOT NULL,
        updated_at        BIGINT         NOT NULL,
        CONSTRAINT FK_call_logs_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE,
        CONSTRAINT FK_call_logs_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id),
        CONSTRAINT FK_call_logs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_call_logs_task FOREIGN KEY (callback_task_id) REFERENCES dbo.tasks(id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.call_logs') AND name = N'IX_call_logs_customer_called_at'
)
    CREATE INDEX IX_call_logs_customer_called_at ON dbo.call_logs (customer_id, called_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.call_logs') AND name = N'IX_call_logs_user_called_at'
)
    CREATE INDEX IX_call_logs_user_called_at ON dbo.call_logs (user_id, called_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.call_logs') AND name = N'IX_call_logs_opportunity'
)
    CREATE INDEX IX_call_logs_opportunity ON dbo.call_logs (opportunity_id);
GO

PRINT 'SCRUM-104 call_logs schema created successfully!';
GO
