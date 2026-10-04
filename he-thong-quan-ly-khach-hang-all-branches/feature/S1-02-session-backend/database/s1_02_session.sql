IF OBJECT_ID(N'dbo.users',N'U') IS NULL
BEGIN
  CREATE TABLE dbo.users(
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(150) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    password_hash NVARCHAR(512) NOT NULL,
    role NVARCHAR(50) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
  );
END;
GO
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dbo.users') AND name=N'UX_users_email')
  CREATE UNIQUE INDEX UX_users_email ON dbo.users(email);
GO
IF OBJECT_ID(N'dbo.login_sessions',N'U') IS NULL
BEGIN
  CREATE TABLE dbo.login_sessions(
    token_hash CHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at BIGINT NOT NULL,
    last_seen_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    revoked_at BIGINT NULL,
    CONSTRAINT FK_login_sessions_users FOREIGN KEY(user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
  );
END;
GO
