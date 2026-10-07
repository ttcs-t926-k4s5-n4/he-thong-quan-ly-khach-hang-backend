SET NOCOUNT ON;

IF OBJECT_ID(N'dbo.business_groups', N'U') IS NULL
CREATE TABLE business_groups(
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(150) NOT NULL UNIQUE
);
GO

IF OBJECT_ID(N'dbo.roles', N'U') IS NULL
CREATE TABLE roles(
    id INT IDENTITY(1,1) PRIMARY KEY,
    code NVARCHAR(50) NOT NULL UNIQUE,
    name NVARCHAR(120) NOT NULL
);
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
CREATE TABLE users(
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(150) NOT NULL,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(512) NOT NULL,
    status NVARCHAR(50) NOT NULL DEFAULT N'pending',
    data_scope NVARCHAR(20) NOT NULL DEFAULT N'self',
    business_group_id INT NULL REFERENCES business_groups(id),
    is_active BIT NOT NULL DEFAULT 1,
    credentials_version INT NOT NULL DEFAULT 1,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.user_roles', N'U') IS NULL
CREATE TABLE user_roles(
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY(user_id, role_id)
);
GO

IF OBJECT_ID(N'dbo.login_sessions', N'U') IS NULL
CREATE TABLE login_sessions(
    token_hash CHAR(64) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credentials_version INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    last_seen_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    expires_at DATETIME2 NOT NULL,
    revoked_at DATETIME2 NULL
);
GO

IF OBJECT_ID(N'dbo.password_reset_tokens', N'U') IS NULL
CREATE TABLE password_reset_tokens(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME2 NOT NULL,
    used_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.account_activation_tokens', N'U') IS NULL
CREATE TABLE account_activation_tokens(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME2 NOT NULL,
    used_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.outbox_emails', N'U') IS NULL
CREATE TABLE outbox_emails(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    recipient NVARCHAR(255) NOT NULL,
    subject NVARCHAR(255) NOT NULL,
    body NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
CREATE TABLE customers(
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    phone NVARCHAR(50) NULL,
    email NVARCHAR(255) NULL,
    owner_id INT NOT NULL REFERENCES users(id),
    business_group_id INT NULL REFERENCES business_groups(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.opportunities', N'U') IS NULL
CREATE TABLE opportunities(
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(255) NOT NULL,
    value DECIMAL(18,2) NOT NULL DEFAULT 0,
    stage NVARCHAR(100) NOT NULL DEFAULT N'Mới',
    owner_id INT NOT NULL REFERENCES users(id),
    business_group_id INT NULL REFERENCES business_groups(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.handover_logs', N'U') IS NULL
CREATE TABLE handover_logs(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    from_user_id INT NOT NULL REFERENCES users(id),
    to_user_id INT NOT NULL REFERENCES users(id),
    admin_id INT NOT NULL REFERENCES users(id),
    customer_count INT NOT NULL,
    opportunity_count INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE OR ALTER VIEW v_user_roles AS
SELECT u.id user_id, r.code role_code, r.name role_name
FROM users u
JOIN user_roles ur ON ur.user_id=u.id
JOIN roles r ON r.id=ur.role_id;
GO

IF OBJECT_ID(N'dbo.activities', N'U') IS NULL
CREATE TABLE activities(
    id INT IDENTITY(1,1) PRIMARY KEY,
    subject NVARCHAR(255) NOT NULL,
    activity_type NVARCHAR(100) NOT NULL,
    owner_id INT NOT NULL REFERENCES users(id),
    business_group_id INT NULL REFERENCES business_groups(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dbo.quotations', N'U') IS NULL
CREATE TABLE quotations(
    id INT IDENTITY(1,1) PRIMARY KEY,
    quote_no NVARCHAR(80) NOT NULL UNIQUE,
    total_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    status NVARCHAR(100) NOT NULL DEFAULT N'Nháp',
    owner_id INT NOT NULL REFERENCES users(id),
    business_group_id INT NULL REFERENCES business_groups(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
