/*
S1-03 - Đặt lại mật khẩu khi quên
SQL Server

Acceptance Criteria:
1. Email hợp lệ và có tài khoản sẽ nhận link đặt lại có hiệu lực 30 phút.
2. Link chỉ dùng được một lần.
3. Email không tồn tại vẫn nhận cùng thông báo từ API.
*/

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password_hash NVARCHAR(512) NOT NULL,
        created_at BIGINT NOT NULL,
        updated_at BIGINT NOT NULL
    );
END;
GO

IF COL_LENGTH('dbo.users', 'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD created_at BIGINT NOT NULL
        CONSTRAINT DF_users_created_at_s103 DEFAULT (0);
END;
GO

IF COL_LENGTH('dbo.users', 'updated_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD updated_at BIGINT NOT NULL
        CONSTRAINT DF_users_updated_at_s103 DEFAULT (0);
END;
GO

IF OBJECT_ID(N'dbo.password_reset_tokens', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.password_reset_tokens (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id INT NOT NULL,
        token_hash CHAR(64) NOT NULL UNIQUE,
        expires_at BIGINT NOT NULL,
        used_at BIGINT NULL,
        created_at BIGINT NOT NULL,
        CONSTRAINT FK_password_reset_tokens_users
            FOREIGN KEY (user_id)
            REFERENCES dbo.users(id)
            ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_password_reset_tokens_user_id'
      AND object_id = OBJECT_ID('dbo.password_reset_tokens')
)
BEGIN
    CREATE INDEX IX_password_reset_tokens_user_id
    ON dbo.password_reset_tokens(user_id);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_password_reset_tokens_token_hash'
      AND object_id = OBJECT_ID('dbo.password_reset_tokens')
)
BEGIN
    CREATE INDEX IX_password_reset_tokens_token_hash
    ON dbo.password_reset_tokens(token_hash);
END;
GO
