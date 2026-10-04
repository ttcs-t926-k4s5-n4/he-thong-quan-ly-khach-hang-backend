/*
S1-10 - Bàn giao dữ liệu và khóa tài khoản
SQL Server

Acceptance Criteria:
1. Tài khoản bị khóa không đăng nhập được và các phiên đang mở bị thu hồi.
2. Bắt buộc chọn người tiếp nhận toàn bộ khách hàng và cơ hội trước khi khóa.
3. Việc bàn giao được ghi nhật ký, dữ liệu không bị mất chủ sở hữu.
*/

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password_hash NVARCHAR(512) NOT NULL,
        role NVARCHAR(30) NOT NULL
            CONSTRAINT DF_users_role DEFAULT (N'user'),
        is_active BIT NOT NULL
            CONSTRAINT DF_users_is_active DEFAULT (1),
        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_users_created_at DEFAULT (SYSUTCDATETIME())
    );
END;
GO

IF COL_LENGTH('dbo.users', 'is_active') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD is_active BIT NOT NULL
        CONSTRAINT DF_users_is_active_s110 DEFAULT (1);
END;
GO

IF OBJECT_ID(N'dbo.sessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sessions (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        token_hash CHAR(64) NOT NULL UNIQUE,
        created_at BIGINT NOT NULL,
        expires_at BIGINT NOT NULL,
        revoked_at BIGINT NULL,
        CONSTRAINT FK_sessions_users
            FOREIGN KEY (user_id)
            REFERENCES dbo.users(id)
            ON DELETE CASCADE
    );
END;
GO

IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        owner_id BIGINT NOT NULL,
        CONSTRAINT FK_customers_owner
            FOREIGN KEY (owner_id)
            REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.opportunities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunities (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        title NVARCHAR(255) NOT NULL,
        owner_id BIGINT NOT NULL,
        CONSTRAINT FK_opportunities_owner
            FOREIGN KEY (owner_id)
            REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.handover_logs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.handover_logs (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        from_user_id BIGINT NOT NULL,
        to_user_id BIGINT NOT NULL,
        admin_id BIGINT NOT NULL,
        customer_count INT NOT NULL,
        opportunity_count INT NOT NULL,
        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_handover_logs_created_at
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT FK_handover_logs_from_user
            FOREIGN KEY (from_user_id)
            REFERENCES dbo.users(id),

        CONSTRAINT FK_handover_logs_to_user
            FOREIGN KEY (to_user_id)
            REFERENCES dbo.users(id),

        CONSTRAINT FK_handover_logs_admin
            FOREIGN KEY (admin_id)
            REFERENCES dbo.users(id)
    );
END;
GO
