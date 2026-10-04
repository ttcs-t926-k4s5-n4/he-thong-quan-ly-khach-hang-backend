/*
S1-08 - Quản lý tài khoản người dùng
SQL Server

Acceptance Criteria:
- Tạo tài khoản và gửi email kích hoạt kèm mật khẩu tạm.
- Email trùng bị từ chối với thông báo cụ thể.
- Tìm theo tên, email, nhóm; lọc theo vai trò và trạng thái.
- Danh sách phân trang mặc định 20 dòng.
*/

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        full_name NVARCHAR(150) NOT NULL,
        email NVARCHAR(255) NOT NULL,
        password_hash NVARCHAR(512) NOT NULL,
        group_name NVARCHAR(120) NOT NULL,
        role_name NVARCHAR(120) NOT NULL,
        status NVARCHAR(50) NOT NULL
            CONSTRAINT DF_users_status DEFAULT (N'Chờ kích hoạt'),
        created_at BIGINT NOT NULL,
        updated_at BIGINT NOT NULL
    );
END;
GO

IF COL_LENGTH('dbo.users', 'full_name') IS NULL
BEGIN
    ALTER TABLE dbo.users ADD full_name NVARCHAR(150) NULL;
END;
GO

IF COL_LENGTH('dbo.users', 'group_name') IS NULL
BEGIN
    ALTER TABLE dbo.users ADD group_name NVARCHAR(120) NULL;
END;
GO

IF COL_LENGTH('dbo.users', 'role_name') IS NULL
BEGIN
    ALTER TABLE dbo.users ADD role_name NVARCHAR(120) NULL;
END;
GO

IF COL_LENGTH('dbo.users', 'status') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD status NVARCHAR(50) NOT NULL
        CONSTRAINT DF_users_status_s108 DEFAULT (N'Chờ kích hoạt');
END;
GO

IF COL_LENGTH('dbo.users', 'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD created_at BIGINT NOT NULL
        CONSTRAINT DF_users_created_at_s108 DEFAULT (0);
END;
GO

IF COL_LENGTH('dbo.users', 'updated_at') IS NULL
BEGIN
    ALTER TABLE dbo.users
    ADD updated_at BIGINT NOT NULL
        CONSTRAINT DF_users_updated_at_s108 DEFAULT (0);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.users')
      AND is_unique = 1
      AND name = N'UX_users_email'
)
BEGIN
    CREATE UNIQUE INDEX UX_users_email ON dbo.users(email);
END;
GO

IF OBJECT_ID(N'dbo.account_activation_tokens', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.account_activation_tokens (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id INT NOT NULL,
        token_hash CHAR(64) NOT NULL UNIQUE,
        expires_at BIGINT NOT NULL,
        used_at BIGINT NULL,
        created_at BIGINT NOT NULL,
        CONSTRAINT FK_account_activation_tokens_users
            FOREIGN KEY (user_id)
            REFERENCES dbo.users(id)
            ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_account_activation_tokens_user_id'
      AND object_id = OBJECT_ID(N'dbo.account_activation_tokens')
)
BEGIN
    CREATE INDEX IX_account_activation_tokens_user_id
    ON dbo.account_activation_tokens(user_id);
END;
GO
