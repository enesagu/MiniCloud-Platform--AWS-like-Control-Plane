-- =====================================================
-- MiniCloud Platform - PostgreSQL Schema
-- AWS-like Resource Registry + IAM + Audit
-- Compatible with backend API
-- =====================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if any (for clean start)
DROP TABLE IF EXISTS role_policies CASCADE;
DROP TABLE IF EXISTS role_bindings CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS metering_usage CASCADE;
DROP TABLE IF EXISTS workflow_runs CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS event_rules CASCADE;
DROP TABLE IF EXISTS resource_versions CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- 1. ORGANIZATIONS
CREATE TABLE organizations (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. PROJECTS
CREATE TABLE projects (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id VARCHAR(255) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    settings JSONB DEFAULT '{}',
    quota JSONB DEFAULT '{"buckets": 10, "functions": 50, "workflows": 100}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 3. USERS
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id VARCHAR(255) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, username)
);

-- 4. ROLES
CREATE TABLE roles (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id VARCHAR(255) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 5. POLICIES
CREATE TABLE policies (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id VARCHAR(255) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version INT DEFAULT 1,
    document JSONB NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 6. ROLE_BINDINGS
CREATE TABLE role_bindings (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id VARCHAR(255) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    project_id VARCHAR(255) REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role_id, project_id)
);

-- 7. ROLE_POLICIES
CREATE TABLE role_policies (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    role_id VARCHAR(255) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    policy_id VARCHAR(255) NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, policy_id)
);

-- 8. RESOURCES (All platform resources)
CREATE TABLE resources (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    spec JSONB DEFAULT '{}',
    state JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, type, name)
);

-- 9. EVENT_RULES
CREATE TABLE event_rules (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    event_pattern JSONB NOT NULL,
    targets JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    trigger_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- 10. AUDIT_LOGS
CREATE TABLE audit_logs (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(255),
    actor_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details TEXT,
    ip_address VARCHAR(50),
    status VARCHAR(50) DEFAULT 'success',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_time ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_org ON audit_logs(org_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- 11. WORKFLOW_RUNS
CREATE TABLE workflow_runs (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workflow_id VARCHAR(255),
    workflow_name VARCHAR(100),
    run_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'RUNNING',
    input JSONB,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id, started_at);

-- 12. METERING_USAGE
CREATE TABLE metering_usage (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(255) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    usage_value DECIMAL(20, 4) NOT NULL,
    usage_unit VARCHAR(20) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 13. API_KEYS
CREATE TABLE api_keys (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SEED DATA
-- =====================================================

-- Default organization
INSERT INTO organizations (id, name, display_name) VALUES 
    ('org-default', 'default', 'Default Organization')
ON CONFLICT (name) DO NOTHING;

-- Default project
INSERT INTO projects (id, org_id, name, display_name) VALUES
    ('proj-default', 'org-default', 'default', 'Default Project')
ON CONFLICT (org_id, name) DO NOTHING;

-- System roles
INSERT INTO roles (id, org_id, name, description, is_system) VALUES
    ('role-admin', 'org-default', 'admin', 'Full access to all resources', TRUE),
    ('role-developer', 'org-default', 'developer', 'Create and manage own resources', TRUE),
    ('role-viewer', 'org-default', 'viewer', 'Read-only access', TRUE)
ON CONFLICT (org_id, name) DO NOTHING;

-- System policies
INSERT INTO policies (id, org_id, name, description, document, is_system) VALUES
    ('policy-admin', 'org-default', 'AdminFullAccess', 'Full access to everything', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}]}', TRUE),
    
    ('policy-developer', 'org-default', 'DeveloperAccess', 'Manage resources in assigned projects', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["resource:*", "function:*", "workflow:*"], "Resource": ["project:*"]}]}', TRUE),
    
    ('policy-viewer', 'org-default', 'ViewerReadOnly', 'Read-only access', 
    '{"Version": "2024-01-01", "Statement": [{"Effect": "Allow", "Action": ["*:Get", "*:List", "*:Describe"], "Resource": ["*"]}]}', TRUE)
ON CONFLICT (org_id, name) DO NOTHING;

-- Bind policies to roles
INSERT INTO role_policies (role_id, policy_id) VALUES
    ('role-admin', 'policy-admin'),
    ('role-developer', 'policy-developer'),
    ('role-viewer', 'policy-viewer')
ON CONFLICT (role_id, policy_id) DO NOTHING;

-- Default admin user
INSERT INTO users (id, org_id, username, email, password_hash) VALUES
    ('user-admin', 'org-default', 'admin', 'admin@minicloud.local', 'hashed_admin123')
ON CONFLICT (org_id, username) DO NOTHING;
