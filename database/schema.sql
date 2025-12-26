-- =====================================================
-- MiniCloud Platform - PostgreSQL Schema
-- AWS-like Resource Registry + IAM + Audit
-- =====================================================

-- 1. ORGANIZATIONS (AWS Organizations benzeri)
CREATE TABLE IF NOT EXISTS orgs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. PROJECTS (AWS Accounts benzeri)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, SUSPENDED, DELETED
    settings JSONB DEFAULT '{}',
    quota JSONB DEFAULT '{"buckets": 10, "functions": 50, "workflows": 100}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(org_id, name)
);

-- 3. USERS (IAM Users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255), -- bcrypt hash
    status VARCHAR(50) DEFAULT 'ACTIVE',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(org_id, username)
);

-- 4. ROLES (IAM Roles)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE, -- Admin, ReadOnly gibi built-in roller
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(org_id, name)
);

-- 5. POLICIES (IAM Policies - AWS IAM Policy Document benzeri)
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version INT DEFAULT 1,
    document JSONB NOT NULL, -- AWS IAM Policy benzeri JSON
    -- Örnek document:
    -- {
    --   "Version": "2024-01-01",
    --   "Statement": [
    --     {
    --       "Effect": "Allow",
    --       "Action": ["minio:GetObject", "minio:PutObject"],
    --       "Resource": ["bucket:raw/*", "bucket:processed/*"],
    --       "Condition": {"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}}
    --     }
    --   ]
    -- }
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(org_id, name)
);

-- 6. ROLE_BINDINGS (Kullanıcıya rol atama)
CREATE TABLE IF NOT EXISTS role_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE, -- NULL ise org-wide
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, role_id, project_id)
);

-- 7. ROLE_POLICIES (Role'a policy bağlama)
CREATE TABLE IF NOT EXISTS role_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(role_id, policy_id)
);

-- 8. RESOURCES (Tüm platform kaynakları: bucket, function, workflow, topic...)
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- bucket, function, workflow, topic, rule, schedule
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, CREATING, DELETING, FAILED
    spec JSONB NOT NULL, -- Kaynak tanımı (config)
    state JSONB DEFAULT '{}', -- Runtime durumu
    tags JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, type, name)
);

-- 9. RESOURCE_VERSIONS (Kaynak versiyonlama - GitOps benzeri)
CREATE TABLE IF NOT EXISTS resource_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    version INT NOT NULL,
    spec JSONB NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(resource_id, version)
);

-- 10. EVENT_RULES (EventBridge benzeri routing kuralları)
CREATE TABLE IF NOT EXISTS event_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'ENABLED', -- ENABLED, DISABLED
    event_pattern JSONB NOT NULL, -- {"source": "minio", "detail-type": "ObjectCreated", "detail": {"bucket": "raw"}}
    targets JSONB NOT NULL, -- [{"type": "workflow", "name": "doc_ingest"}, {"type": "function", "name": "notify"}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, name)
);

-- 11. AUDIT_LOG (CloudTrail benzeri - append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    project_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL, -- resource:Create, resource:Delete, auth:Login, policy:Evaluate
    resource_type VARCHAR(50),
    resource_id UUID,
    resource_name VARCHAR(255),
    request_params JSONB,
    response_status VARCHAR(50), -- SUCCESS, DENIED, FAILED
    source_ip VARCHAR(50),
    user_agent TEXT,
    event_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log için partition veya index
CREATE INDEX idx_audit_log_time ON audit_log(event_time);
CREATE INDEX idx_audit_log_org ON audit_log(org_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- 12. METERING_USAGE (Kullanım takibi - billing için)
CREATE TABLE IF NOT EXISTS metering_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- storage_gb, function_invocations, workflow_runs
    usage_value DECIMAL(20, 4) NOT NULL,
    usage_unit VARCHAR(20) NOT NULL, -- GB, count, seconds
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metering_project ON metering_usage(project_id, period_start);

-- 13. API_KEYS (Programatic access)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL, -- SHA256 hash of the key
    key_prefix VARCHAR(10) NOT NULL, -- İlk 8 karakter (gösterim için)
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 14. WORKFLOW_RUNS (Temporal workflow execution history - local cache)
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    workflow_name VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL, -- Temporal workflow ID
    run_id VARCHAR(255), -- Temporal run ID
    status VARCHAR(50) NOT NULL, -- RUNNING, COMPLETED, FAILED, CANCELLED
    input JSONB,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workflow_runs_project ON workflow_runs(project_id, started_at);

-- =====================================================
-- SEED DATA: Default system roles & policies
-- =====================================================

-- Default organization
INSERT INTO orgs (id, name, display_name) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'default', 'Default Organization')
ON CONFLICT DO NOTHING;

-- System roles
INSERT INTO roles (id, org_id, name, description, is_system) VALUES
    ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'admin', 'Full access to all resources', TRUE),
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'developer', 'Create and manage own resources', TRUE),
    ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'viewer', 'Read-only access', TRUE)
ON CONFLICT DO NOTHING;

-- System policies
INSERT INTO policies (id, org_id, name, description, document, is_system) VALUES
    ('00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000001', 'AdminFullAccess', 'Full access to everything', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}]}', TRUE),
    
    ('00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000001', 'DeveloperAccess', 'Manage resources in assigned projects', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["resource:*", "function:*", "workflow:*"], "Resource": ["project:${project_id}/*"]}]}', TRUE),
    
    ('00000000-0000-0000-0000-000000000022', '00000000-0000-0000-0000-000000000001', 'ViewerReadOnly', 'Read-only access', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["*:Get", "*:List", "*:Describe"], "Resource": ["*"]}]}', TRUE)
ON CONFLICT DO NOTHING;

-- Bind policies to roles
INSERT INTO role_policies (role_id, policy_id) VALUES
    ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000020'),
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000021'),
    ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000022')
ON CONFLICT DO NOTHING;
