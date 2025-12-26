-- =====================================================
-- MiniCloud Platform - PostgreSQL Schema
-- AWS-like Resource Registry + IAM + Audit
-- All IDs are TEXT (not UUID) for simpler usage
-- =====================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if any (for clean start)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS queues CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
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
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. PROJECTS
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    status TEXT DEFAULT 'ACTIVE',
    settings JSONB DEFAULT '{}',
    quota JSONB DEFAULT '{"buckets": 10, "functions": 50, "workflows": 100}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 3. USERS
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    username TEXT NOT NULL,
    email TEXT,
    password_hash TEXT,
    status TEXT DEFAULT 'ACTIVE',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, username)
);

-- 4. ROLES
CREATE TABLE roles (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 5. POLICIES
CREATE TABLE policies (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    version INT DEFAULT 1,
    document JSONB NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, name)
);

-- 6. ROLE_BINDINGS
CREATE TABLE role_bindings (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    project_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role_id, project_id)
);

-- 7. ROLE_POLICIES
CREATE TABLE role_policies (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    role_id TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, policy_id)
);

-- 8. RESOURCES (All platform resources)
CREATE TABLE resources (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    spec JSONB DEFAULT '{}',
    state JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, type, name)
);

-- 9. EVENT_RULES
CREATE TABLE event_rules (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
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
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_id TEXT NOT NULL,
    project_id TEXT,
    actor_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    status TEXT DEFAULT 'success',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_time ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_org ON audit_logs(org_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- 11. WORKFLOW_RUNS
CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workflow_id TEXT,
    workflow_name TEXT,
    run_id TEXT,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    input JSONB,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id, started_at);

-- 12. METERING_USAGE
CREATE TABLE metering_usage (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    usage_value DECIMAL(20, 4) NOT NULL,
    usage_unit TEXT NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 13. API_KEYS
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- COMPUTE (EC2-like Instance Management)
-- =====================================================

-- 14. HOSTS (Compute nodes in the cluster)
CREATE TABLE hosts (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    ip_address TEXT,
    zone TEXT DEFAULT 'default',
    cpu_total INT NOT NULL DEFAULT 8,
    cpu_allocated INT NOT NULL DEFAULT 0,
    memory_total_mb INT NOT NULL DEFAULT 16384,
    memory_allocated_mb INT NOT NULL DEFAULT 0,
    disk_total_gb INT NOT NULL DEFAULT 500,
    disk_allocated_gb INT NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',
    agent_version TEXT,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hosts_status ON hosts(status);

-- 15. INSTANCES (Virtual machines/containers)
CREATE TABLE instances (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    
    -- Compute Specs
    cpu INT NOT NULL DEFAULT 2,
    memory_mb INT NOT NULL DEFAULT 2048,
    disk_gb INT NOT NULL DEFAULT 20,
    image TEXT NOT NULL DEFAULT 'ubuntu:22.04',
    
    -- Placement
    host_id TEXT REFERENCES hosts(id),
    zone TEXT DEFAULT 'default',
    
    -- Network
    network_segment TEXT DEFAULT 'default',
    ip_address TEXT,
    dns_name TEXT,
    
    -- State Machine (see InstanceState enum in workers/instance_workflows.py)
    state TEXT NOT NULL DEFAULT 'REQUESTED',
    state_message TEXT,
    
    -- Lifecycle
    startup_script TEXT,
    tags JSONB DEFAULT '{}',
    
    -- Workflow Tracking
    workflow_run_id TEXT,
    
    -- Timestamps
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provisioned_at TIMESTAMP WITH TIME ZONE,
    running_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    terminated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, name)
);

CREATE INDEX idx_instances_project ON instances(project_id);
CREATE INDEX idx_instances_state ON instances(state);
CREATE INDEX idx_instances_host ON instances(host_id);

-- 16. INSTANCE_EVENTS (State transition audit trail)
CREATE TABLE instance_events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    instance_id TEXT NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
    from_state TEXT,
    to_state TEXT NOT NULL,
    message TEXT,
    actor_id TEXT DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instance_events_instance ON instance_events(instance_id, created_at);

-- =====================================================
-- MESSAGING (SNS/SQS equivalent)
-- =====================================================

-- 14. TOPICS (SNS-like pub/sub)
CREATE TABLE topics (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    message_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- 15. SUBSCRIPTIONS (Topic subscribers)
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    topic_id TEXT NOT NULL,
    protocol TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    filter_policy JSONB DEFAULT '{}',
    delivery_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_topic ON subscriptions(topic_id);

-- 16. QUEUES (SQS-like message queues)
CREATE TABLE queues (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    visibility_timeout INT DEFAULT 30,
    message_retention INT DEFAULT 345600,
    max_message_size INT DEFAULT 262144,
    delay_seconds INT DEFAULT 0,
    receive_count BIGINT DEFAULT 0,
    message_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- 17. MESSAGES (Queue messages)
CREATE TABLE messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    queue_id TEXT NOT NULL,
    body TEXT NOT NULL,
    attributes JSONB DEFAULT '{}',
    message_group_id TEXT,
    receipt_handle TEXT,
    visible_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    receive_count INT DEFAULT 0,
    first_received_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_messages_queue ON messages(queue_id, visible_at);

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

-- Default compute hosts (simulated cluster)
INSERT INTO hosts (id, name, hostname, ip_address, zone, cpu_total, memory_total_mb, disk_total_gb, status) VALUES
    ('host-001', 'compute-node-1', 'node1.minicloud.local', '192.168.1.101', 'zone-a', 16, 32768, 500, 'ACTIVE'),
    ('host-002', 'compute-node-2', 'node2.minicloud.local', '192.168.1.102', 'zone-a', 16, 32768, 500, 'ACTIVE'),
    ('host-003', 'compute-node-3', 'node3.minicloud.local', '192.168.1.103', 'zone-b', 32, 65536, 1000, 'ACTIVE'),
    ('host-004', 'compute-node-4', 'node4.minicloud.local', '192.168.1.104', 'zone-b', 8, 16384, 250, 'ACTIVE')
ON CONFLICT (name) DO NOTHING;

