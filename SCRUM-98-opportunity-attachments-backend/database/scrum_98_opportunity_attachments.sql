-- =============================================================================
-- Migration: SCRUM-98 ΓÇö ─É├¡nh k├¿m t├ái liß╗çu v├áo C╞í hß╗Öi kinh doanh (Opportunity Documents)
-- Database: crm_db | SQL Server 2019+
-- =============================================================================

IF OBJECT_ID(N'dbo.opportunity_documents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.opportunity_documents (
        id               BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
        opportunity_id   INT            NOT NULL,
        original_name    NVARCHAR(255)  NOT NULL,
        stored_filename  NVARCHAR(255)  NOT NULL UNIQUE,
        storage_path     NVARCHAR(500)  NOT NULL,
        file_size        BIGINT         NOT NULL,
        file_format      NVARCHAR(50)   NOT NULL,
        mime_type        NVARCHAR(100)  NOT NULL,
        uploaded_by      INT            NOT NULL,
        uploaded_at      BIGINT         NOT NULL,
        is_deleted       BIT            NOT NULL CONSTRAINT DF_opp_doc_is_deleted DEFAULT (0),
        deleted_at       BIGINT         NULL,
        deleted_by       INT            NULL,
        CONSTRAINT FK_opp_doc_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
        CONSTRAINT FK_opp_doc_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES dbo.users(id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_documents') AND name = N'IX_opp_doc_opp_id_uploaded_at'
)
    CREATE INDEX IX_opp_doc_opp_id_uploaded_at ON dbo.opportunity_documents (opportunity_id, uploaded_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.opportunity_documents') AND name = N'IX_opp_doc_uploaded_by'
)
    CREATE INDEX IX_opp_doc_uploaded_by ON dbo.opportunity_documents (uploaded_by);
GO

PRINT 'SCRUM-98 opportunity_documents schema created successfully!';
GO
