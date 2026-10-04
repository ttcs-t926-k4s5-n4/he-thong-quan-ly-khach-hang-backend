/*
S1-09 - Gán vai trò và người dùng vào nhóm kinh doanh
SQL Server

Acceptance Criteria:
1. Một người dùng có thể giữ nhiều vai trò cùng lúc.
2. Người giữ vai trò Trưởng nhóm phải được gán một nhóm cụ thể.
3. Không thể tự thu hồi vai trò Quản trị của chính mình.
*/

IF OBJECT_ID(N'dbo.business_groups', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.business_groups (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(150) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'dbo.roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        code NVARCHAR(50) NOT NULL UNIQUE,
        name NVARCHAR(120) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        full_name NVARCHAR(150) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        business_group_id INT NULL,
        CONSTRAINT FK_users_business_groups
            FOREIGN KEY (business_group_id)
            REFERENCES dbo.business_groups(id)
    );
END;
GO

IF COL_LENGTH('dbo.users', 'business_group_id') IS NULL
BEGIN
    ALTER TABLE dbo.users ADD business_group_id INT NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_users_business_groups'
)
BEGIN
    ALTER TABLE dbo.users
    ADD CONSTRAINT FK_users_business_groups
        FOREIGN KEY (business_group_id)
        REFERENCES dbo.business_groups(id);
END;
GO

IF OBJECT_ID(N'dbo.user_roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.user_roles (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        CONSTRAINT PK_user_roles PRIMARY KEY (user_id, role_id),
        CONSTRAINT FK_user_roles_users
            FOREIGN KEY (user_id)
            REFERENCES dbo.users(id)
            ON DELETE CASCADE,
        CONSTRAINT FK_user_roles_roles
            FOREIGN KEY (role_id)
            REFERENCES dbo.roles(id)
            ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.roles WHERE code = N'ADMIN')
    INSERT INTO dbo.roles(code, name) VALUES (N'ADMIN', N'Quản trị hệ thống');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.roles WHERE code = N'TEAM_LEADER')
    INSERT INTO dbo.roles(code, name) VALUES (N'TEAM_LEADER', N'Trưởng nhóm');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.roles WHERE code = N'SALES')
    INSERT INTO dbo.roles(code, name) VALUES (N'SALES', N'Nhân viên kinh doanh');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.roles WHERE code = N'REPORT_VIEWER')
    INSERT INTO dbo.roles(code, name) VALUES (N'REPORT_VIEWER', N'Xem báo cáo');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.business_groups WHERE name = N'Nhóm Kinh doanh 1')
    INSERT INTO dbo.business_groups(name) VALUES (N'Nhóm Kinh doanh 1');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.business_groups WHERE name = N'Nhóm Kinh doanh 2')
    INSERT INTO dbo.business_groups(name) VALUES (N'Nhóm Kinh doanh 2');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = N'admin@company.vn')
    INSERT INTO dbo.users(full_name, email, business_group_id)
    VALUES (N'Quản trị viên', N'admin@company.vn', NULL);
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.user_roles ur
    INNER JOIN dbo.users u ON u.id = ur.user_id
    INNER JOIN dbo.roles r ON r.id = ur.role_id
    WHERE u.email = N'admin@company.vn'
      AND r.code = N'ADMIN'
)
BEGIN
    INSERT INTO dbo.user_roles(user_id, role_id)
    SELECT u.id, r.id
    FROM dbo.users u
    CROSS JOIN dbo.roles r
    WHERE u.email = N'admin@company.vn'
      AND r.code = N'ADMIN';
END;
GO
