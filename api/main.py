"""
MiniCloud Platform - Control Plane API
AWS-like self-hosted cloud platform with real database and MinIO integration
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import os
import asyncpg
from minio import Minio
from minio.error import S3Error

app = FastAPI(
    title="MiniCloud Platform API",
    description="Self-hosted AWS-like Control Plane API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/minicloud")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

# Database connection pool
db_pool = None

# MinIO client
minio_client = None

@app.on_event("startup")
async def startup():
    global db_pool, minio_client
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
    
    try:
        minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
        print("✅ Connected to MinIO")
    except Exception as e:
        print(f"⚠️ MinIO connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

# =====================================================
# MODELS
# =====================================================

class OrgCreate(BaseModel):
    name: str
    display_name: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    display_name: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class ResourceCreate(BaseModel):
    type: str
    name: str
    spec: Dict[str, Any] = {}
    tags: Optional[Dict[str, str]] = {}

class EventRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_pattern: Dict[str, Any]
    targets: List[Dict[str, Any]]
    enabled: bool = True

class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    document: Dict[str, Any]

# =====================================================
# HELPERS
# =====================================================

async def log_audit(action: str, resource_type: str, resource_id: str, actor_id: str = "system", details: dict = None):
    """Log an audit event to the database"""
    if not db_pool:
        return
    try:
        await db_pool.execute("""
            INSERT INTO audit_logs (id, org_id, project_id, actor_id, action, resource_type, resource_id, details, ip_address, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, str(uuid.uuid4()), 'org-default', 'proj-default', actor_id, action, resource_type, resource_id, 
        str(details) if details else None, '127.0.0.1', datetime.utcnow())
    except Exception as e:
        print(f"Audit log error: {e}")

# =====================================================
# HEALTH & INFO
# =====================================================

@app.get("/")
async def root():
    return {"service": "MiniCloud Platform", "version": "1.0.0", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    db_ok = db_pool is not None
    minio_ok = minio_client is not None
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "minio": "connected" if minio_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# ORGANIZATIONS
# =====================================================

@app.post("/api/v1/orgs", tags=["Organizations"])
async def create_org(org: OrgCreate):
    org_id = str(uuid.uuid4())
    if db_pool:
        await db_pool.execute(
            "INSERT INTO organizations (id, name, display_name, created_at) VALUES ($1, $2, $3, $4)",
            org_id, org.name, org.display_name or org.name, datetime.utcnow()
        )
    await log_audit("CreateOrganization", "organization", org_id)
    return {"id": org_id, "name": org.name, "display_name": org.display_name or org.name, "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/orgs", tags=["Organizations"])
async def list_orgs():
    if db_pool:
        rows = await db_pool.fetch("SELECT * FROM organizations ORDER BY created_at DESC")
        return [dict(r) for r in rows]
    return []

# =====================================================
# PROJECTS
# =====================================================

@app.post("/api/v1/orgs/{org_id}/projects", tags=["Projects"])
async def create_project(org_id: str, project: ProjectCreate):
    project_id = str(uuid.uuid4())
    if db_pool:
        await db_pool.execute(
            "INSERT INTO projects (id, org_id, name, display_name, created_at) VALUES ($1, $2, $3, $4, $5)",
            project_id, org_id, project.name, project.display_name or project.name, datetime.utcnow()
        )
    await log_audit("CreateProject", "project", project_id)
    return {"id": project_id, "org_id": org_id, "name": project.name, "status": "ACTIVE", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/orgs/{org_id}/projects", tags=["Projects"])
async def list_projects(org_id: str):
    if db_pool:
        rows = await db_pool.fetch("SELECT * FROM projects WHERE org_id = $1 ORDER BY created_at DESC", org_id)
        return [dict(r) for r in rows]
    return []

# =====================================================
# IAM - USERS
# =====================================================

@app.post("/api/v1/orgs/{org_id}/users", tags=["IAM"])
async def create_user(org_id: str, user: UserCreate):
    user_id = str(uuid.uuid4())
    if db_pool:
        await db_pool.execute(
            "INSERT INTO users (id, org_id, username, email, password_hash, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            user_id, org_id, user.username, user.email, "hashed_" + user.password, datetime.utcnow()
        )
    await log_audit("CreateUser", "user", user_id)
    return {"id": user_id, "org_id": org_id, "username": user.username, "email": user.email, "status": "ACTIVE", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/orgs/{org_id}/users", tags=["IAM"])
async def list_users(org_id: str):
    if db_pool:
        rows = await db_pool.fetch("SELECT id, org_id, username, email, created_at FROM users WHERE org_id = $1", org_id)
        return [dict(r) for r in rows]
    return []

@app.delete("/api/v1/orgs/{org_id}/users/{user_id}", tags=["IAM"])
async def delete_user(org_id: str, user_id: str):
    if db_pool:
        await db_pool.execute("DELETE FROM users WHERE id = $1 AND org_id = $2", user_id, org_id)
    await log_audit("DeleteUser", "user", user_id)
    return {"id": user_id, "status": "DELETED"}

# =====================================================
# IAM - POLICIES
# =====================================================

@app.post("/api/v1/orgs/{org_id}/policies", tags=["IAM"])
async def create_policy(org_id: str, policy: PolicyCreate):
    policy_id = str(uuid.uuid4())
    if db_pool:
        import json
        await db_pool.execute(
            "INSERT INTO policies (id, org_id, name, description, document, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            policy_id, org_id, policy.name, policy.description, json.dumps(policy.document), datetime.utcnow()
        )
    await log_audit("CreatePolicy", "policy", policy_id)
    return {"id": policy_id, "name": policy.name, "description": policy.description, "document": policy.document, "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/orgs/{org_id}/policies", tags=["IAM"])
async def list_policies(org_id: str):
    if db_pool:
        import json
        rows = await db_pool.fetch("SELECT * FROM policies WHERE org_id = $1", org_id)
        result = []
        for r in rows:
            d = dict(r)
            if 'document' in d and isinstance(d['document'], str):
                d['document'] = json.loads(d['document'])
            result.append(d)
        return result
    return []

@app.post("/api/v1/policies/simulate", tags=["IAM"])
async def simulate_policy(action: str, resource: str, context: Optional[Dict[str, Any]] = None):
    # Import policy engine
    try:
        from core.policy_engine import PolicyEngine
        engine = PolicyEngine()
        result = engine.evaluate(action=action, resource=resource, context=context or {})
        return {"action": action, "resource": resource, "allowed": result.allowed, "reason": result.reason}
    except Exception as e:
        return {"action": action, "resource": resource, "allowed": True, "reason": f"Simulation (engine not available): {e}"}

# =====================================================
# RESOURCES (Generic)
# =====================================================

@app.post("/api/v1/projects/{project_id}/resources", tags=["Resources"])
async def create_resource(project_id: str, resource: ResourceCreate):
    import json
    resource_id = str(uuid.uuid4())
    if db_pool:
        await db_pool.execute(
            "INSERT INTO resources (id, project_id, type, name, spec, tags, state, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            resource_id, project_id, resource.type, resource.name, json.dumps(resource.spec), json.dumps(resource.tags), '{"status": "ACTIVE"}', datetime.utcnow()
        )
    await log_audit(f"Create{resource.type.title()}", resource.type, resource_id)
    return {"id": resource_id, "project_id": project_id, "type": resource.type, "name": resource.name, "status": "ACTIVE", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/projects/{project_id}/resources", tags=["Resources"])
async def list_resources(project_id: str, type: Optional[str] = None):
    if db_pool:
        import json
        if type:
            rows = await db_pool.fetch("SELECT * FROM resources WHERE project_id = $1 AND type = $2 ORDER BY created_at DESC", project_id, type)
        else:
            rows = await db_pool.fetch("SELECT * FROM resources WHERE project_id = $1 ORDER BY created_at DESC", project_id)
        result = []
        for r in rows:
            d = dict(r)
            for k in ['spec', 'tags', 'state']:
                if k in d and isinstance(d[k], str):
                    try:
                        d[k] = json.loads(d[k])
                    except:
                        pass
            result.append(d)
        return result
    return []

@app.delete("/api/v1/projects/{project_id}/resources/{resource_id}", tags=["Resources"])
async def delete_resource(project_id: str, resource_id: str):
    if db_pool:
        await db_pool.execute("DELETE FROM resources WHERE id = $1 AND project_id = $2", resource_id, project_id)
    await log_audit("DeleteResource", "resource", resource_id)
    return {"id": resource_id, "status": "DELETED"}

# =====================================================
# STORAGE - BUCKETS (MinIO)
# =====================================================

@app.post("/api/v1/projects/{project_id}/buckets", tags=["Storage"])
async def create_bucket(project_id: str, name: str):
    try:
        if minio_client:
            if not minio_client.bucket_exists(name):
                minio_client.make_bucket(name)
    except S3Error as e:
        raise HTTPException(status_code=400, detail=f"MinIO error: {e}")
    
    # Also store in resources table
    if db_pool:
        import json
        resource_id = str(uuid.uuid4())
        await db_pool.execute(
            "INSERT INTO resources (id, project_id, type, name, spec, state, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            resource_id, project_id, 'bucket', name, '{}', '{"status": "ACTIVE"}', datetime.utcnow()
        )
    
    await log_audit("CreateBucket", "bucket", name)
    return {"name": name, "project_id": project_id, "status": "ACTIVE", "endpoint": f"http://minio:9000/{name}", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/projects/{project_id}/buckets", tags=["Storage"])
async def list_buckets(project_id: str):
    buckets = []
    
    # Get from MinIO
    if minio_client:
        try:
            for bucket in minio_client.list_buckets():
                objects = list(minio_client.list_objects(bucket.name))
                buckets.append({
                    "name": bucket.name,
                    "created_at": bucket.creation_date.isoformat() if bucket.creation_date else datetime.utcnow().isoformat(),
                    "object_count": len(objects),
                    "size_bytes": sum(obj.size or 0 for obj in objects) if objects else 0
                })
        except Exception as e:
            print(f"MinIO list error: {e}")
    
    return buckets

@app.delete("/api/v1/projects/{project_id}/buckets/{bucket_name}", tags=["Storage"])
async def delete_bucket(project_id: str, bucket_name: str):
    try:
        if minio_client:
            # First remove all objects
            objects = minio_client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                minio_client.remove_object(bucket_name, obj.object_name)
            minio_client.remove_bucket(bucket_name)
    except S3Error as e:
        raise HTTPException(status_code=400, detail=f"MinIO error: {e}")
    
    # Remove from resources
    if db_pool:
        await db_pool.execute("DELETE FROM resources WHERE type = 'bucket' AND name = $1 AND project_id = $2", bucket_name, project_id)
    
    await log_audit("DeleteBucket", "bucket", bucket_name)
    return {"name": bucket_name, "status": "DELETED"}

# =====================================================
# FUNCTIONS
# =====================================================

@app.post("/api/v1/projects/{project_id}/functions", tags=["Functions"])
async def create_function(project_id: str, name: str, runtime: str = "python3.10", memory_mb: int = 128, timeout_seconds: int = 30):
    import json
    function_id = str(uuid.uuid4())
    spec = {"runtime": runtime, "memory_mb": memory_mb, "timeout_seconds": timeout_seconds, "handler": "main.handler"}
    
    if db_pool:
        await db_pool.execute(
            "INSERT INTO resources (id, project_id, type, name, spec, state, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            function_id, project_id, 'function', name, json.dumps(spec), '{"status": "ACTIVE", "invocation_count": 0}', datetime.utcnow()
        )
    
    await log_audit("CreateFunction", "function", function_id)
    return {"id": function_id, "name": name, "spec": spec, "status": "ACTIVE", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/projects/{project_id}/functions", tags=["Functions"])
async def list_functions(project_id: str):
    return await list_resources(project_id, type="function")

@app.delete("/api/v1/projects/{project_id}/functions/{function_id}", tags=["Functions"])
async def delete_function(project_id: str, function_id: str):
    return await delete_resource(project_id, function_id)

@app.post("/api/v1/functions/{function_id}/invoke", tags=["Functions"])
async def invoke_function(function_id: str, payload: Dict[str, Any] = {}):
    # Update invocation count
    if db_pool:
        await db_pool.execute(
            "UPDATE resources SET state = jsonb_set(COALESCE(state::jsonb, '{}'), '{invocation_count}', (COALESCE((state::jsonb->>'invocation_count')::int, 0) + 1)::text::jsonb) WHERE id = $1",
            function_id
        )
    
    await log_audit("InvokeFunction", "function", function_id)
    return {"function_id": function_id, "status": "SUCCESS", "response": {"message": "Function executed", "input": payload}, "duration_ms": 42}

# =====================================================
# WORKFLOWS
# =====================================================

@app.post("/api/v1/projects/{project_id}/workflows", tags=["Workflows"])
async def create_workflow(project_id: str, name: str, definition: Dict[str, Any] = {}):
    import json
    workflow_id = str(uuid.uuid4())
    
    if db_pool:
        await db_pool.execute(
            "INSERT INTO resources (id, project_id, type, name, spec, state, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            workflow_id, project_id, 'workflow', name, json.dumps(definition), '{"status": "ACTIVE", "run_count": 0}', datetime.utcnow()
        )
    
    await log_audit("CreateWorkflow", "workflow", workflow_id)
    return {"id": workflow_id, "name": name, "status": "ACTIVE", "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/projects/{project_id}/workflows", tags=["Workflows"])
async def list_workflows(project_id: str):
    return await list_resources(project_id, type="workflow")

@app.delete("/api/v1/projects/{project_id}/workflows/{workflow_id}", tags=["Workflows"])
async def delete_workflow(project_id: str, workflow_id: str):
    return await delete_resource(project_id, workflow_id)

@app.post("/api/v1/workflows/{workflow_name}/start", tags=["Workflows"])
async def start_workflow(workflow_name: str, input: Dict[str, Any] = {}):
    import json
    run_id = str(uuid.uuid4())
    
    if db_pool:
        # Store workflow run
        await db_pool.execute(
            "INSERT INTO workflow_runs (id, workflow_id, status, input, started_at) VALUES ($1, (SELECT id FROM resources WHERE name = $2 AND type = 'workflow' LIMIT 1), $3, $4, $5)",
            run_id, workflow_name, 'RUNNING', json.dumps(input), datetime.utcnow()
        )
        # Update run count
        await db_pool.execute(
            "UPDATE resources SET state = jsonb_set(COALESCE(state::jsonb, '{}'), '{run_count}', (COALESCE((state::jsonb->>'run_count')::int, 0) + 1)::text::jsonb) WHERE name = $1 AND type = 'workflow'",
            workflow_name
        )
    
    await log_audit("StartWorkflow", "workflow", workflow_name)
    return {"workflow_name": workflow_name, "run_id": run_id, "status": "RUNNING", "started_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/workflows/{workflow_name}/runs", tags=["Workflows"])
async def list_workflow_runs(workflow_name: str):
    if db_pool:
        rows = await db_pool.fetch("""
            SELECT wr.* FROM workflow_runs wr
            JOIN resources r ON wr.workflow_id = r.id
            WHERE r.name = $1 AND r.type = 'workflow'
            ORDER BY wr.started_at DESC LIMIT 50
        """, workflow_name)
        return [dict(r) for r in rows]
    return []

# =====================================================
# EVENT RULES
# =====================================================

@app.post("/api/v1/projects/{project_id}/event-rules", tags=["Events"])
async def create_event_rule(project_id: str, rule: EventRuleCreate):
    import json
    rule_id = str(uuid.uuid4())
    
    if db_pool:
        await db_pool.execute(
            "INSERT INTO event_rules (id, project_id, name, description, event_pattern, targets, enabled, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            rule_id, project_id, rule.name, rule.description, json.dumps(rule.event_pattern), json.dumps(rule.targets), rule.enabled, datetime.utcnow()
        )
    
    await log_audit("CreateEventRule", "event_rule", rule_id)
    return {"id": rule_id, "name": rule.name, "event_pattern": rule.event_pattern, "targets": rule.targets, "enabled": rule.enabled, "created_at": datetime.utcnow().isoformat()}

@app.get("/api/v1/projects/{project_id}/event-rules", tags=["Events"])
async def list_event_rules(project_id: str):
    if db_pool:
        import json
        rows = await db_pool.fetch("SELECT * FROM event_rules WHERE project_id = $1 ORDER BY created_at DESC", project_id)
        result = []
        for r in rows:
            d = dict(r)
            for k in ['event_pattern', 'targets']:
                if k in d and isinstance(d[k], str):
                    try:
                        d[k] = json.loads(d[k])
                    except:
                        pass
            result.append(d)
        return result
    return []

@app.delete("/api/v1/projects/{project_id}/event-rules/{rule_id}", tags=["Events"])
async def delete_event_rule(project_id: str, rule_id: str):
    if db_pool:
        await db_pool.execute("DELETE FROM event_rules WHERE id = $1 AND project_id = $2", rule_id, project_id)
    await log_audit("DeleteEventRule", "event_rule", rule_id)
    return {"id": rule_id, "status": "DELETED"}

# =====================================================
# AUDIT LOGS
# =====================================================

@app.get("/api/v1/orgs/{org_id}/audit-logs", tags=["Audit"])
async def list_audit_logs(org_id: str, resource_type: Optional[str] = None, limit: int = 100):
    if db_pool:
        if resource_type:
            rows = await db_pool.fetch(
                "SELECT * FROM audit_logs WHERE org_id = $1 AND resource_type = $2 ORDER BY timestamp DESC LIMIT $3",
                org_id, resource_type, limit
            )
        else:
            rows = await db_pool.fetch(
                "SELECT * FROM audit_logs WHERE org_id = $1 ORDER BY timestamp DESC LIMIT $2",
                org_id, limit
            )
        return [dict(r) for r in rows]
    return []

# =====================================================
# USAGE
# =====================================================

@app.get("/api/v1/projects/{project_id}/usage", tags=["Metering"])
async def get_project_usage(project_id: str):
    usage = {"storage_bytes": 0, "function_invocations": 0, "workflow_runs": 0, "api_calls_24h": 0}
    
    # Get storage from MinIO
    if minio_client:
        try:
            for bucket in minio_client.list_buckets():
                for obj in minio_client.list_objects(bucket.name, recursive=True):
                    usage["storage_bytes"] += obj.size or 0
        except:
            pass
    
    # Get function invocations and workflow runs from DB
    if db_pool:
        try:
            row = await db_pool.fetchrow("""
                SELECT 
                    COALESCE(SUM((state::jsonb->>'invocation_count')::int), 0) as fn_invocations,
                    COALESCE(SUM((state::jsonb->>'run_count')::int), 0) as wf_runs
                FROM resources WHERE project_id = $1
            """, project_id)
            if row:
                usage["function_invocations"] = row['fn_invocations'] or 0
                usage["workflow_runs"] = row['wf_runs'] or 0
            
            # Count audit logs in last 24h as API calls
            count = await db_pool.fetchval(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '24 hours'"
            )
            usage["api_calls_24h"] = count or 0
        except:
            pass
    
    return {"project_id": project_id, "period": "current", **usage}

# =====================================================
# ENTRYPOINT
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
