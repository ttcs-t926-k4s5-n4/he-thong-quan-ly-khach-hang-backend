IF OBJECT_ID(N'dbo.users',N'U') IS NULL
BEGIN
  CREATE TABLE dbo.users(
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(150) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    password_hash NVARCHAR(512) NOT NULL,
    role NVARCHAR(50) NOT NULL,
    failed_login_attempts INT NOT NULL DEFAULT(0),
    locked_until BIGINT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
  );
END;
GO
IF COL_LENGTH('dbo.users','failed_login_attempts') IS NULL
  ALTER TABLE dbo.users ADD failed_login_attempts INT NOT NULL DEFAULT(0);
GO
IF COL_LENGTH('dbo.users','locked_until') IS NULL
  ALTER TABLE dbo.users ADD locked_until BIGINT NULL;
GO
IF COL_LENGTH('dbo.users','role') IS NULL
  ALTER TABLE dbo.users ADD role NVARCHAR(50) NOT NULL DEFAULT(N'employee');
GO
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dbo.users') AND name=N'UX_users_email')
  CREATE UNIQUE INDEX UX_users_email ON dbo.users(email);
GO
