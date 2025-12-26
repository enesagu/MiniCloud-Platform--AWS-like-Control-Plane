"""
MiniCloud Platform - API Routers
HTTP endpoints following Single Responsibility Principle
Each router handles one domain only
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    OrgCreate, ProjectCreate, UserCreate, PolicyCreate,
    ResourceCreate, EventRuleCreate,
    TopicCreate, SubscriptionCreate, QueueCreate, MessageCreate
)
from .services import ServiceFactory
from .database import db, storage

# =====================================================
# HEALTH & METRICS ROUTER
# =====================================================

health_router = APIRouter(tags=["Health"])


@health_router.get("/")
async def root():
    return {
        "service": "MiniCloud Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@health_router.get("/health")
async def health_check():
    return {
        "status": "healthy" if db.is_connected else "degraded",
        "database": "connected" if db.is_connected else "disconnected",
        "minio": "connected" if storage.is_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@health_router.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_service = ServiceFactory.get_metrics_service()
    
    lines = [
        "# HELP minicloud_up API is up",
        "# TYPE minicloud_up gauge",
        "minicloud_up 1",
        "# HELP minicloud_database_connected Database connection status",
        "# TYPE minicloud_database_connected gauge",
        f"minicloud_database_connected {1 if db.is_connected else 0}",
        "# HELP minicloud_minio_connected MinIO connection status",
        "# TYPE minicloud_minio_connected gauge",
        f"minicloud_minio_connected {1 if storage.is_connected else 0}",
    ]
    
    counts = await metrics_service.get_resource_counts()
    lines.extend([
        "# HELP minicloud_resources_total Total resources by type",
        "# TYPE minicloud_resources_total gauge",
        f'minicloud_resources_total{{type="function"}} {counts.get("functions", 0)}',
        f'minicloud_resources_total{{type="workflow"}} {counts.get("workflows", 0)}',
        f'minicloud_resources_total{{type="bucket"}} {counts.get("buckets", 0)}',
        f'minicloud_resources_total{{type="topic"}} {counts.get("topics", 0)}',
        f'minicloud_resources_total{{type="queue"}} {counts.get("queues", 0)}',
    ])
    
    return PlainTextResponse("\n".join(lines), media_type="text/plain")


# =====================================================
# ORGANIZATIONS ROUTER
# =====================================================

org_router = APIRouter(prefix="/api/v1/orgs", tags=["Organizations"])


@org_router.post("")
async def create_org(org: OrgCreate):
    service = ServiceFactory.get_organization_service()
    return await service.create(org.name, org.display_name)


@org_router.get("")
async def list_orgs():
    service = ServiceFactory.get_organization_service()
    return await service.list_all()


# =====================================================
# PROJECTS ROUTER
# =====================================================

project_router = APIRouter(prefix="/api/v1/orgs/{org_id}/projects", tags=["Projects"])


@project_router.post("")
async def create_project(org_id: str, project: ProjectCreate):
    service = ServiceFactory.get_project_service()
    return await service.create(org_id, project.name, project.display_name)


@project_router.get("")
async def list_projects(org_id: str):
    service = ServiceFactory.get_project_service()
    return await service.list_by_org(org_id)


# =====================================================
# USERS ROUTER
# =====================================================

user_router = APIRouter(prefix="/api/v1/orgs/{org_id}/users", tags=["IAM"])


@user_router.post("")
async def create_user(org_id: str, user: UserCreate):
    service = ServiceFactory.get_user_service()
    return await service.create(org_id, user.username, user.email, user.password)


@user_router.get("")
async def list_users(org_id: str):
    service = ServiceFactory.get_user_service()
    return await service.list_by_org(org_id)


@user_router.delete("/{user_id}")
async def delete_user(org_id: str, user_id: str):
    service = ServiceFactory.get_user_service()
    return await service.delete(org_id, user_id)


# =====================================================
# POLICIES ROUTER
# =====================================================

policy_router = APIRouter(prefix="/api/v1", tags=["IAM"])


@policy_router.post("/orgs/{org_id}/policies")
async def create_policy(org_id: str, policy: PolicyCreate):
    service = ServiceFactory.get_policy_service()
    return await service.create(org_id, policy.name, policy.description, policy.document)


@policy_router.get("/orgs/{org_id}/policies")
async def list_policies(org_id: str):
    service = ServiceFactory.get_policy_service()
    return await service.list_by_org(org_id)


@policy_router.post("/policies/simulate")
async def simulate_policy(
    action: str = Query(...),
    resource: str = Query(...),
    context: Dict[str, Any] = None
):
    service = ServiceFactory.get_policy_service()
    return await service.simulate(action, resource, context or {})


# =====================================================
# RESOURCES ROUTER
# =====================================================

resource_router = APIRouter(prefix="/api/v1/projects/{project_id}/resources", tags=["Resources"])


@resource_router.post("")
async def create_resource(project_id: str, resource: ResourceCreate):
    service = ServiceFactory.get_resource_service()
    return await service.create(project_id, resource.type, resource.name, resource.spec, resource.tags)


@resource_router.get("")
async def list_resources(project_id: str, type: Optional[str] = None):
    service = ServiceFactory.get_resource_service()
    return await service.list_by_project(project_id, type)


@resource_router.delete("/{resource_id}")
async def delete_resource(project_id: str, resource_id: str):
    service = ServiceFactory.get_resource_service()
    return await service.delete(project_id, resource_id)


# =====================================================
# BUCKETS ROUTER
# =====================================================

bucket_router = APIRouter(prefix="/api/v1/projects/{project_id}/buckets", tags=["Storage"])


@bucket_router.post("")
async def create_bucket(project_id: str, name: str = Query(...)):
    service = ServiceFactory.get_storage_service()
    try:
        return await service.create_bucket(project_id, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@bucket_router.get("")
async def list_buckets(project_id: str):
    service = ServiceFactory.get_storage_service()
    return await service.list_buckets(project_id)


@bucket_router.delete("/{bucket_name}")
async def delete_bucket(project_id: str, bucket_name: str):
    service = ServiceFactory.get_storage_service()
    try:
        return await service.delete_bucket(project_id, bucket_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================
# FUNCTIONS ROUTER
# =====================================================

function_router = APIRouter(prefix="/api/v1", tags=["Functions"])


@function_router.post("/projects/{project_id}/functions")
async def create_function(
    project_id: str,
    name: str = Query(...),
    runtime: str = Query("python3.10"),
    memory_mb: int = Query(128),
    timeout_seconds: int = Query(30),
    body: Dict[str, Any] = None
):
    service = ServiceFactory.get_function_service()
    code = body.get("code", "") if body else ""
    return await service.create(project_id, name, runtime, memory_mb, timeout_seconds, code)


@function_router.get("/projects/{project_id}/functions")
async def list_functions(project_id: str):
    service = ServiceFactory.get_function_service()
    return await service.list_by_project(project_id)


@function_router.get("/projects/{project_id}/functions/{function_id}")
async def get_function(project_id: str, function_id: str):
    service = ServiceFactory.get_function_service()
    return await service.get(project_id, function_id)


@function_router.delete("/projects/{project_id}/functions/{function_id}")
async def delete_function(project_id: str, function_id: str):
    service = ServiceFactory.get_function_service()
    return await service.delete(project_id, function_id)


@function_router.put("/functions/{function_id}/code")
async def update_function_code(function_id: str, body: Dict[str, Any]):
    """Update function code"""
    service = ServiceFactory.get_function_service()
    code = body.get("code", "")
    return await service.update_code(function_id, code)


@function_router.post("/functions/{function_id}/invoke")
async def invoke_function(function_id: str, payload: Dict[str, Any] = None):
    service = ServiceFactory.get_function_service()
    return await service.invoke(function_id, payload or {})


# =====================================================
# WORKFLOWS ROUTER
# =====================================================

workflow_router = APIRouter(prefix="/api/v1", tags=["Workflows"])


@workflow_router.post("/projects/{project_id}/workflows")
async def create_workflow(project_id: str, name: str = Query(...), definition: Dict[str, Any] = None):
    service = ServiceFactory.get_workflow_service()
    return await service.create(project_id, name, definition)


@workflow_router.get("/projects/{project_id}/workflows")
async def list_workflows(project_id: str):
    service = ServiceFactory.get_workflow_service()
    return await service.list_by_project(project_id)


@workflow_router.delete("/projects/{project_id}/workflows/{workflow_id}")
async def delete_workflow(project_id: str, workflow_id: str):
    service = ServiceFactory.get_workflow_service()
    return await service.delete(project_id, workflow_id)


@workflow_router.post("/workflows/{workflow_name}/start")
async def start_workflow(workflow_name: str, input_data: Dict[str, Any] = None):
    service = ServiceFactory.get_workflow_service()
    return await service.start(workflow_name, input_data)


@workflow_router.get("/workflows/{workflow_name}/runs")
async def list_workflow_runs(workflow_name: str):
    service = ServiceFactory.get_workflow_service()
    return await service.list_runs(workflow_name)


# =====================================================
# EVENT RULES ROUTER
# =====================================================

event_router = APIRouter(prefix="/api/v1/projects/{project_id}/event-rules", tags=["Events"])


@event_router.post("")
async def create_event_rule(project_id: str, rule: EventRuleCreate):
    service = ServiceFactory.get_event_rule_service()
    return await service.create(
        project_id, rule.name, rule.description,
        rule.event_pattern, rule.targets, rule.enabled
    )


@event_router.get("")
async def list_event_rules(project_id: str):
    service = ServiceFactory.get_event_rule_service()
    return await service.list_by_project(project_id)


@event_router.delete("/{rule_id}")
async def delete_event_rule(project_id: str, rule_id: str):
    service = ServiceFactory.get_event_rule_service()
    return await service.delete(project_id, rule_id)


# =====================================================
# TOPICS ROUTER (SNS)
# =====================================================

topic_router = APIRouter(prefix="/api/v1", tags=["Topics"])


@topic_router.post("/projects/{project_id}/topics")
async def create_topic(project_id: str, topic: TopicCreate):
    service = ServiceFactory.get_topic_service()
    return await service.create(project_id, topic.name, topic.display_name, topic.description)


@topic_router.get("/projects/{project_id}/topics")
async def list_topics(project_id: str):
    service = ServiceFactory.get_topic_service()
    return await service.list_by_project(project_id)


@topic_router.delete("/projects/{project_id}/topics/{topic_id}")
async def delete_topic(project_id: str, topic_id: str):
    service = ServiceFactory.get_topic_service()
    return await service.delete(project_id, topic_id)


@topic_router.post("/topics/{topic_id}/publish")
async def publish_to_topic(topic_id: str, message: MessageCreate):
    service = ServiceFactory.get_topic_service()
    return await service.publish(topic_id, message.body, message.attributes)


# =====================================================
# SUBSCRIPTIONS ROUTER
# =====================================================

subscription_router = APIRouter(prefix="/api/v1", tags=["Topics"])


@subscription_router.post("/topics/{topic_id}/subscriptions")
async def create_subscription(topic_id: str, sub: SubscriptionCreate):
    service = ServiceFactory.get_subscription_service()
    return await service.create(topic_id, sub.protocol, sub.endpoint, sub.filter_policy)


@subscription_router.get("/topics/{topic_id}/subscriptions")
async def list_subscriptions(topic_id: str):
    service = ServiceFactory.get_subscription_service()
    return await service.list_by_topic(topic_id)


@subscription_router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    service = ServiceFactory.get_subscription_service()
    return await service.delete(subscription_id)


# =====================================================
# QUEUES ROUTER (SQS)
# =====================================================

queue_router = APIRouter(prefix="/api/v1", tags=["Queues"])


@queue_router.post("/projects/{project_id}/queues")
async def create_queue(project_id: str, queue: QueueCreate):
    service = ServiceFactory.get_queue_service()
    return await service.create(
        project_id, queue.name, queue.description,
        queue.visibility_timeout, queue.message_retention, queue.delay_seconds
    )


@queue_router.get("/projects/{project_id}/queues")
async def list_queues(project_id: str):
    service = ServiceFactory.get_queue_service()
    return await service.list_by_project(project_id)


@queue_router.get("/queues/{queue_id}")
async def get_queue(queue_id: str):
    service = ServiceFactory.get_queue_service()
    try:
        return await service.get(queue_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@queue_router.delete("/projects/{project_id}/queues/{queue_id}")
async def delete_queue(project_id: str, queue_id: str):
    service = ServiceFactory.get_queue_service()
    return await service.delete(project_id, queue_id)


@queue_router.post("/queues/{queue_id}/messages")
async def send_message(queue_id: str, message: MessageCreate):
    service = ServiceFactory.get_queue_service()
    return await service.send_message(
        queue_id, message.body, message.attributes, message.delay_seconds or 0
    )


@queue_router.get("/queues/{queue_id}/messages")
async def receive_messages(
    queue_id: str,
    max_messages: int = Query(1),
    visibility_timeout: int = Query(30)
):
    service = ServiceFactory.get_queue_service()
    return await service.receive_messages(queue_id, max_messages, visibility_timeout)


@queue_router.delete("/queues/{queue_id}/messages/{receipt_handle}")
async def delete_message(queue_id: str, receipt_handle: str):
    service = ServiceFactory.get_queue_service()
    return await service.delete_message(queue_id, receipt_handle)


@queue_router.post("/queues/{queue_id}/purge")
async def purge_queue(queue_id: str):
    service = ServiceFactory.get_queue_service()
    return await service.purge(queue_id)


# =====================================================
# AUDIT LOGS ROUTER
# =====================================================

audit_router = APIRouter(prefix="/api/v1/orgs/{org_id}/audit-logs", tags=["Audit"])


@audit_router.get("")
async def list_audit_logs(
    org_id: str,
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100)
):
    service = ServiceFactory.get_audit_service()
    return await service.list_by_org(org_id, resource_type, limit)


# =====================================================
# USAGE ROUTER
# =====================================================

usage_router = APIRouter(prefix="/api/v1/projects/{project_id}/usage", tags=["Metering"])


@usage_router.get("")
async def get_usage(project_id: str):
    service = ServiceFactory.get_metrics_service()
    return await service.get_usage(project_id)


# =====================================================
# ROUTER COLLECTION
# =====================================================

all_routers = [
    health_router,
    org_router,
    project_router,
    user_router,
    policy_router,
    resource_router,
    bucket_router,
    function_router,
    workflow_router,
    event_router,
    topic_router,
    subscription_router,
    queue_router,
    audit_router,
    usage_router,
]
