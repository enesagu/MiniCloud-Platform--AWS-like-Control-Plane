"""
MiniCloud Platform - Pydantic Models
Request/Response schemas following Interface Segregation Principle
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


# =====================================================
# BASE MODELS
# =====================================================

class BaseResponse(BaseModel):
    """Base response with common fields"""
    id: str
    created_at: str


class DeleteResponse(BaseModel):
    """Standard delete response"""
    id: str
    status: str = "DELETED"


# =====================================================
# ORGANIZATIONS
# =====================================================

class OrgCreate(BaseModel):
    name: str
    display_name: Optional[str] = None


class OrgResponse(BaseResponse):
    name: str
    display_name: str


# =====================================================
# PROJECTS
# =====================================================

class ProjectCreate(BaseModel):
    name: str
    display_name: Optional[str] = None


class ProjectResponse(BaseResponse):
    org_id: str
    name: str
    status: str = "ACTIVE"


# =====================================================
# IAM - USERS
# =====================================================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseResponse):
    org_id: str
    username: str
    email: str
    status: str = "ACTIVE"


# =====================================================
# IAM - POLICIES
# =====================================================

class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    document: Dict[str, Any]


class PolicyResponse(BaseResponse):
    name: str
    description: Optional[str]
    document: Dict[str, Any]


class PolicySimulateResponse(BaseModel):
    action: str
    resource: str
    allowed: bool
    reason: str


# =====================================================
# RESOURCES
# =====================================================

class ResourceCreate(BaseModel):
    type: str
    name: str
    spec: Dict[str, Any] = {}
    tags: Optional[Dict[str, str]] = {}


class ResourceResponse(BaseResponse):
    project_id: str
    type: str
    name: str
    status: str = "ACTIVE"


# =====================================================
# FUNCTIONS
# =====================================================

class FunctionCreate(BaseModel):
    name: str
    runtime: str = "python3.10"
    memory_mb: int = 128
    timeout_seconds: int = 30


class FunctionResponse(BaseResponse):
    name: str
    spec: Dict[str, Any]
    status: str = "ACTIVE"


class FunctionInvokeResponse(BaseModel):
    function_id: str
    status: str
    response: Dict[str, Any]
    duration_ms: int


# =====================================================
# WORKFLOWS
# =====================================================

class WorkflowCreate(BaseModel):
    name: str
    definition: Dict[str, Any] = {}


class WorkflowResponse(BaseResponse):
    name: str
    status: str = "ACTIVE"


class WorkflowStartResponse(BaseModel):
    workflow_name: str
    run_id: str
    status: str = "RUNNING"
    started_at: str


# =====================================================
# EVENT RULES
# =====================================================

class EventRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_pattern: Dict[str, Any]
    targets: List[Dict[str, Any]]
    enabled: bool = True


class EventRuleResponse(BaseResponse):
    name: str
    event_pattern: Dict[str, Any]
    targets: List[Dict[str, Any]]
    enabled: bool


# =====================================================
# MESSAGING - TOPICS (SNS)
# =====================================================

class TopicCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None


class TopicResponse(BaseResponse):
    name: str
    arn: str


class SubscriptionCreate(BaseModel):
    protocol: str  # http, https, email, sqs, lambda
    endpoint: str
    filter_policy: Optional[Dict[str, Any]] = {}


class SubscriptionResponse(BaseResponse):
    topic_id: str
    protocol: str
    endpoint: str
    status: str = "CONFIRMED"


class PublishResponse(BaseModel):
    message_id: str
    topic_id: str
    delivered_to: int


# =====================================================
# MESSAGING - QUEUES (SQS)
# =====================================================

class QueueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    visibility_timeout: int = 30
    message_retention: int = 345600
    delay_seconds: int = 0


class QueueResponse(BaseResponse):
    name: str
    url: str
    arn: str


class MessageCreate(BaseModel):
    body: str
    attributes: Optional[Dict[str, Any]] = {}
    delay_seconds: Optional[int] = 0


class MessageResponse(BaseModel):
    message_id: str
    queue_id: str
    body: str
    sent_at: str


class ReceiveMessagesResponse(BaseModel):
    messages: List[Dict[str, Any]]
    count: int


# =====================================================
# AUDIT
# =====================================================

class AuditLogEntry(BaseModel):
    id: str
    org_id: str
    project_id: Optional[str]
    actor_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    timestamp: str


# =====================================================
# HEALTH & METRICS
# =====================================================

class HealthResponse(BaseModel):
    status: str
    database: str
    minio: str
    timestamp: str


class UsageResponse(BaseModel):
    project_id: str
    period: str
    storage_bytes: int = 0
    function_invocations: int = 0
    workflow_runs: int = 0
    api_calls_24h: int = 0


# =====================================================
# COMPUTE - INSTANCES (EC2-like)
# =====================================================

class InstanceCreate(BaseModel):
    """Create instance request - EC2 RunInstances equivalent"""
    name: str
    display_name: Optional[str] = None
    cpu: int = 2
    memory_mb: int = 2048
    disk_gb: int = 20
    image: str = "ubuntu:22.04"
    network_segment: str = "default"
    zone: Optional[str] = None
    startup_script: Optional[str] = ""
    tags: Optional[Dict[str, str]] = {}
    sla_timeout_seconds: int = 120


class InstanceResponse(BaseResponse):
    """Instance details response"""
    project_id: str
    name: str
    display_name: Optional[str]
    cpu: int
    memory_mb: int
    disk_gb: int
    image: str
    state: str
    ip_address: Optional[str]
    dns_name: Optional[str]
    host_id: Optional[str]
    zone: Optional[str]
    tags: Dict[str, str] = {}


class InstanceStateChange(BaseModel):
    """Instance state change request"""
    action: str  # stop, start, terminate, reboot


class InstanceListResponse(BaseModel):
    """List instances response"""
    instances: List[Dict[str, Any]]
    count: int


# =====================================================
# COMPUTE - HOSTS
# =====================================================

class HostResponse(BaseModel):
    """Compute host details"""
    id: str
    name: str
    hostname: str
    ip_address: Optional[str]
    zone: str
    cpu_total: int
    cpu_allocated: int
    cpu_available: int
    memory_total_mb: int
    memory_allocated_mb: int
    memory_available_mb: int
    status: str
    instance_count: int = 0

