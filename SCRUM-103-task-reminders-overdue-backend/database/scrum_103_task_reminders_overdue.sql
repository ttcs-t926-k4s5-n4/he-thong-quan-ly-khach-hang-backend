-- =============================================================================
-- Migration: SCRUM-103 — Nhắc việc sắp đến hạn & Việc quá hạn (Task Reminders & Overdue)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

-- 1. Bảng dbo.tasks
IF OBJECT_ID(N'dbo.tasks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tasks (
        id               INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
        title            NVARCHAR(250)  NOT NULL,
        description      NVARCHAR(MAX)  NULL,
        assigned_to      INT            NOT NULL,
        created_by       INT            NOT NULL,
        customer_id      INT            NULL,
        opportunity_id   INT            NULL,
        due_date         BIGINT         NOT NULL,
        priority         NVARCHAR(50)   NOT NULL CONSTRAINT DF_tasks_priority DEFAULT (N'medium'),
        status           NVARCHAR(50)   NOT NULL CONSTRAINT DF_tasks_status DEFAULT (N'pending'),
        completed_at     BIGINT         NULL,
        created_at       BIGINT         NOT NULL,
        updated_at       BIGINT         NOT NULL,
        CONSTRAINT FK_tasks_assigned_to FOREIGN KEY (assigned_to) REFERENCES dbo.users(id),
        CONSTRAINT FK_tasks_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_tasks_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
        CONSTRAINT FK_tasks_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.tasks') AND name = N'IX_tasks_assigned_to_due_date'
)
    CREATE INDEX IX_tasks_assigned_to_due_date ON dbo.tasks (assigned_to, status, due_date ASC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.tasks') AND name = N'IX_tasks_status_due_date'
)
    CREATE INDEX IX_tasks_status_due_date ON dbo.tasks (status, due_date ASC);
GO

-- 2. Bảng dbo.notifications
IF OBJECT_ID(N'dbo.notifications', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.notifications (
        id                  BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id             INT            NOT NULL,
        title               NVARCHAR(250)  NOT NULL,
        message             NVARCHAR(MAX)  NOT NULL,
        type                NVARCHAR(50)   NOT NULL CONSTRAINT DF_notif_type DEFAULT (N'task_reminder'),
        reference_type      NVARCHAR(50)   NULL,
        reference_id        INT            NULL,
        reminder_milestone  NVARCHAR(50)   NULL,
        is_read             BIT            NOT NULL CONSTRAINT DF_notif_is_read DEFAULT (0),
        read_at             BIGINT         NULL,
        created_at          BIGINT         NOT NULL,
        CONSTRAINT FK_notif_user FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.notifications') AND name = N'IX_notif_user_read_created'
)
    CREATE INDEX IX_notif_user_read_created ON dbo.notifications (user_id, is_read, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.notifications') AND name = N'UX_notif_dedup'
)
    CREATE UNIQUE INDEX UX_notif_dedup ON dbo.notifications (user_id, reference_type, reference_id, reminder_milestone)
    WHERE reference_id IS NOT NULL AND reminder_milestone IS NOT NULL;
GO

-- 3. Bảng dbo.task_reminder_settings
IF OBJECT_ID(N'dbo.task_reminder_settings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.task_reminder_settings (
        id                      INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id                 INT           NOT NULL UNIQUE,
        milestones_json         NVARCHAR(255) NOT NULL CONSTRAINT DF_trs_milestones DEFAULT (N'["24h", "1h"]'),
        is_email_notification   BIT           NOT NULL CONSTRAINT DF_trs_email DEFAULT (0),
        created_at              BIGINT        NOT NULL,
        updated_at              BIGINT        NOT NULL,
        CONSTRAINT FK_trs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO

PRINT 'SCRUM-103 tasks, notifications & reminder settings schema created successfully!';
GO
