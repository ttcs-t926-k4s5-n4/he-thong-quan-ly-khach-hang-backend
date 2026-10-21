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

-- ===== Sprint 2 + Sprint 3 extensions =====
IF COL_LENGTH('dbo.users','phone') IS NULL ALTER TABLE users ADD phone NVARCHAR(30) NULL;
IF COL_LENGTH('dbo.users','email_signature') IS NULL ALTER TABLE users ADD email_signature NVARCHAR(MAX) NULL;
IF COL_LENGTH('dbo.users','avatar_path') IS NULL ALTER TABLE users ADD avatar_path NVARCHAR(500) NULL;
IF COL_LENGTH('dbo.users','avatar_thumb_path') IS NULL ALTER TABLE users ADD avatar_thumb_path NVARCHAR(500) NULL;
GO
IF COL_LENGTH('dbo.business_groups','parent_id') IS NULL ALTER TABLE business_groups ADD parent_id INT NULL;
IF COL_LENGTH('dbo.business_groups','leader_id') IS NULL ALTER TABLE business_groups ADD leader_id INT NULL;
IF COL_LENGTH('dbo.business_groups','region') IS NULL ALTER TABLE business_groups ADD region NVARCHAR(150) NULL;
GO
IF COL_LENGTH('dbo.customers','tax_code') IS NULL ALTER TABLE customers ADD tax_code NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.customers','industry') IS NULL ALTER TABLE customers ADD industry NVARCHAR(150) NULL;
IF COL_LENGTH('dbo.customers','company_size') IS NULL ALTER TABLE customers ADD company_size NVARCHAR(80) NULL;
IF COL_LENGTH('dbo.customers','website') IS NULL ALTER TABLE customers ADD website NVARCHAR(255) NULL;
IF COL_LENGTH('dbo.customers','address') IS NULL ALTER TABLE customers ADD address NVARCHAR(500) NULL;
IF COL_LENGTH('dbo.customers','status') IS NULL ALTER TABLE customers ADD status NVARCHAR(50) NOT NULL CONSTRAINT DF_customers_status DEFAULT N'Tiềm năng';
IF COL_LENGTH('dbo.customers','parent_customer_id') IS NULL ALTER TABLE customers ADD parent_customer_id INT NULL;
IF COL_LENGTH('dbo.customers','last_interaction_at') IS NULL ALTER TABLE customers ADD last_interaction_at DATETIME2 NULL;
GO
IF COL_LENGTH('dbo.opportunities','customer_id') IS NULL ALTER TABLE opportunities ADD customer_id INT NULL;
IF COL_LENGTH('dbo.opportunities','win_probability') IS NULL ALTER TABLE opportunities ADD win_probability INT NOT NULL CONSTRAINT DF_opps_prob DEFAULT 10;
IF COL_LENGTH('dbo.opportunities','result_type') IS NULL ALTER TABLE opportunities ADD result_type NVARCHAR(20) NULL;
IF COL_LENGTH('dbo.opportunities','result_reason') IS NULL ALTER TABLE opportunities ADD result_reason NVARCHAR(255) NULL;
IF COL_LENGTH('dbo.opportunities','competitor') IS NULL ALTER TABLE opportunities ADD competitor NVARCHAR(255) NULL;
GO
IF COL_LENGTH('dbo.activities','customer_id') IS NULL ALTER TABLE activities ADD customer_id INT NULL;
GO
IF OBJECT_ID(N'dbo.audit_logs',N'U') IS NULL CREATE TABLE audit_logs(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,user_id INT NULL,action NVARCHAR(80) NOT NULL,entity_type NVARCHAR(80) NOT NULL,entity_id INT NULL,
 field_name NVARCHAR(120) NULL,old_value NVARCHAR(MAX) NULL,new_value NVARCHAR(MAX) NULL,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
IF OBJECT_ID(N'dbo.products',N'U') IS NULL CREATE TABLE products(
 id INT IDENTITY(1,1) PRIMARY KEY,code NVARCHAR(60) NOT NULL UNIQUE,name NVARCHAR(255) NOT NULL,product_type NVARCHAR(30) NOT NULL,
 unit NVARCHAR(80) NOT NULL,list_price DECIMAL(18,2) NOT NULL,floor_price DECIMAL(18,2) NOT NULL,is_active BIT NOT NULL DEFAULT 1,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
IF OBJECT_ID(N'dbo.sales_categories',N'U') IS NULL CREATE TABLE sales_categories(
 id INT IDENTITY(1,1) PRIMARY KEY,category_type NVARCHAR(80) NOT NULL,value NVARCHAR(255) NOT NULL,sort_order INT NOT NULL DEFAULT 0,is_active BIT NOT NULL DEFAULT 1,
 CONSTRAINT UQ_sales_category UNIQUE(category_type,value));
GO
IF OBJECT_ID(N'dbo.custom_fields',N'U') IS NULL CREATE TABLE custom_fields(
 id INT IDENTITY(1,1) PRIMARY KEY,entity_type NVARCHAR(30) NOT NULL,field_name NVARCHAR(120) NOT NULL,field_type NVARCHAR(20) NOT NULL,is_required BIT NOT NULL DEFAULT 0,
 options_json NVARCHAR(MAX) NULL,sort_order INT NOT NULL DEFAULT 0,is_active BIT NOT NULL DEFAULT 1);
GO
IF OBJECT_ID(N'dbo.pipeline_stages',N'U') IS NULL CREATE TABLE pipeline_stages(
 id INT IDENTITY(1,1) PRIMARY KEY,name NVARCHAR(150) NOT NULL UNIQUE,sort_order INT NOT NULL,win_probability INT NOT NULL,exit_condition NVARCHAR(500) NULL,is_active BIT NOT NULL DEFAULT 1);
GO
IF OBJECT_ID(N'dbo.win_loss_reasons',N'U') IS NULL CREATE TABLE win_loss_reasons(
 id INT IDENTITY(1,1) PRIMARY KEY,result_type NVARCHAR(20) NOT NULL,reason NVARCHAR(255) NOT NULL,sort_order INT NOT NULL DEFAULT 0,is_active BIT NOT NULL DEFAULT 1);
GO
IF OBJECT_ID(N'dbo.contacts',N'U') IS NULL CREATE TABLE contacts(
 id INT IDENTITY(1,1) PRIMARY KEY,customer_id INT NOT NULL REFERENCES customers(id),full_name NVARCHAR(150) NOT NULL,title NVARCHAR(150) NULL,email NVARCHAR(255) NULL,phone NVARCHAR(30) NULL,
 buying_role NVARCHAR(80) NULL,is_primary BIT NOT NULL DEFAULT 0,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
IF OBJECT_ID(N'dbo.contact_company_history',N'U') IS NULL CREATE TABLE contact_company_history(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,contact_id INT NOT NULL REFERENCES contacts(id),customer_id INT NOT NULL REFERENCES customers(id),company_name NVARCHAR(255) NOT NULL,
 from_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),to_at DATETIME2 NULL);
GO
IF OBJECT_ID(N'dbo.customer_files',N'U') IS NULL CREATE TABLE customer_files(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,customer_id INT NOT NULL REFERENCES customers(id),file_name NVARCHAR(255) NOT NULL,file_path NVARCHAR(500) NOT NULL,file_size BIGINT NOT NULL,
 uploader_id INT NULL,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
IF OBJECT_ID(N'dbo.support_tickets',N'U') IS NULL CREATE TABLE support_tickets(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,customer_id INT NOT NULL REFERENCES customers(id),title NVARCHAR(255) NOT NULL,priority NVARCHAR(30) NOT NULL,status NVARCHAR(30) NOT NULL DEFAULT N'Mở',
 assignee_id INT NULL,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),closed_at DATETIME2 NULL);
GO
IF OBJECT_ID(N'dbo.saved_customer_filters',N'U') IS NULL CREATE TABLE saved_customer_filters(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,user_id INT NOT NULL REFERENCES users(id),name NVARCHAR(150) NOT NULL,filter_json NVARCHAR(MAX) NOT NULL,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
IF OBJECT_ID(N'dbo.care_logs',N'U') IS NULL CREATE TABLE care_logs(
 id BIGINT IDENTITY(1,1) PRIMARY KEY,customer_id INT NOT NULL REFERENCES customers(id),user_id INT NOT NULL REFERENCES users(id),note NVARCHAR(500) NULL,created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());
GO
