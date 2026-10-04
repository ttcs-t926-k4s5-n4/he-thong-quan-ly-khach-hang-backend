/*
S1-04 - Đổi mật khẩu khi đang đăng nhập
SQL Server schema/migration.

Giả định dự án đã có bảng dbo.users với ít nhất:
- id
- email
- password_hash

Script này bổ sung credentials_version nếu còn thiếu
và tạo bảng login_sessions để quản lý/thu hồi phiên.
*/

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password_hash NVARCHAR(512) NOT NULL,
        credentials_version INT NOT NULL
            CONSTRAINT DF_users_credentials_version DEFAULT (1),
        created_at BIGINT NOT NULL,
        updated_at BIGINT NOT NULL
    );
END;
GO

IF COL_LENGTH('dbo.users', 'credentials_version') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD credentials_version INT NOT NULL
        CONSTRAINT DF_users_credentials_version_migration DEFAULT (1);
END;
GO

IF COL_LENGTH('dbo.users', 'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD created_at BIGINT NOT NULL
        CONSTRAINT DF_users_created_at_migration DEFAULT (0);
END;
GO

IF COL_LENGTH('dbo.users', 'updated_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD updated_at BIGINT NOT NULL
        CONSTRAINT DF_users_updated_at_migration DEFAULT (0);
END;
GO

IF OBJECT_ID(N'dbo.login_sessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.login_sessions (
        token_hash CHAR(64) NOT NULL PRIMARY KEY,
        user_id INT NOT NULL,
        credentials_version INT NOT NULL,
        created_at BIGINT NOT NULL,
        last_seen_at BIGINT NOT NULL,
        expires_at BIGINT NOT NULL,
        revoked_at BIGINT NULL,
        CONSTRAINT FK_login_sessions_users
            FOREIGN KEY (user_id)
            REFERENCES dbo.users(id)
            ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_login_sessions_user_id'
      AND object_id = OBJECT_ID('dbo.login_sessions')
)
BEGIN
    CREATE INDEX IX_login_sessions_user_id
    ON dbo.login_sessions(user_id);
END;
GO
