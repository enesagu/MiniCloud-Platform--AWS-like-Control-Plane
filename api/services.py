"""
MiniCloud Platform - Service Layer
Business logic following Single Responsibility and Open/Closed Principles
"""
from abc import ABC
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json

from .repositories import RepositoryFactory
from .database import db, storage
from .config import app_config


class BaseService(ABC):
    """Abstract base service"""
    
    async def _log_audit(self, action: str, resource_type: str, resource_id: str):
        """Log an audit event"""
        audit_repo = RepositoryFactory.get_audit_repo()
        try:
            await audit_repo.create(action, resource_type, resource_id)
        except Exception as e:
            print(f"Audit log error: {e}")


class OrganizationService(BaseService):
    """Business logic for organizations"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_organization_repo()
    
    async def create(self, name: str, display_name: str = None) -> Dict:
        org_id = str(uuid.uuid4())
        display = display_name or name
        
        if db.is_connected:
            await self.repo.create(org_id, name, display)
        
        await self._log_audit("CreateOrganization", "organization", org_id)
        
        return {
            "id": org_id,
            "name": name,
            "display_name": display,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_all(self) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_all()
        return []


class ProjectService(BaseService):
    """Business logic for projects"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_project_repo()
    
    async def create(self, org_id: str, name: str, display_name: str = None) -> Dict:
        project_id = str(uuid.uuid4())
        display = display_name or name
        
        if db.is_connected:
            await self.repo.create(project_id, org_id, name, display)
        
        await self._log_audit("CreateProject", "project", project_id)
        
        return {
            "id": project_id,
            "org_id": org_id,
            "name": name,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_org(org_id)
        return []


class UserService(BaseService):
    """Business logic for IAM users"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_user_repo()
    
    async def create(self, org_id: str, username: str, email: str, password: str) -> Dict:
        user_id = str(uuid.uuid4())
        password_hash = f"hashed_{password}"  # In production, use proper hashing
        
        if db.is_connected:
            await self.repo.create(user_id, org_id, username, email, password_hash)
        
        await self._log_audit("CreateUser", "user", user_id)
        
        return {
            "id": user_id,
            "org_id": org_id,
            "username": username,
            "email": email,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_org(org_id)
        return []
    
    async def delete(self, org_id: str, user_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(org_id, user_id)
        
        await self._log_audit("DeleteUser", "user", user_id)
        return {"id": user_id, "status": "DELETED"}


class PolicyService(BaseService):
    """Business logic for IAM policies"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_policy_repo()
    
    async def create(self, org_id: str, name: str, description: str, document: Dict) -> Dict:
        policy_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(policy_id, org_id, name, description, document)
        
        await self._log_audit("CreatePolicy", "policy", policy_id)
        
        return {
            "id": policy_id,
            "name": name,
            "description": description,
            "document": document,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_org(org_id)
        return []
    
    async def simulate(self, action: str, resource: str, context: Dict = None) -> Dict:
        """Simulate policy evaluation"""
        # Simplified simulation - in production, use full policy engine
        return {
            "action": action,
            "resource": resource,
            "allowed": True,
            "reason": "Simulation: default allow for admin"
        }


class ResourceService(BaseService):
    """Business logic for generic resources"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_resource_repo()
    
    async def create(self, project_id: str, resource_type: str, name: str, 
                    spec: Dict = None, tags: Dict = None) -> Dict:
        resource_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(resource_id, project_id, resource_type, name, spec or {}, tags=tags)
        
        await self._log_audit(f"Create{resource_type.title()}", resource_type, resource_id)
        
        return {
            "id": resource_id,
            "project_id": project_id,
            "type": resource_type,
            "name": name,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str, resource_type: str = None) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_project(project_id, resource_type)
        return []
    
    async def delete(self, project_id: str, resource_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(project_id, resource_id)
        
        await self._log_audit("DeleteResource", "resource", resource_id)
        return {"id": resource_id, "status": "DELETED"}


class StorageService(BaseService):
    """Business logic for MinIO buckets"""
    
    def __init__(self):
        self.resource_repo = RepositoryFactory.get_resource_repo()
    
    async def create_bucket(self, project_id: str, name: str) -> Dict:
        from minio.error import S3Error
        
        # Create in MinIO
        if storage.is_connected:
            try:
                if not storage.client.bucket_exists(name):
                    storage.client.make_bucket(name)
            except S3Error as e:
                raise ValueError(f"MinIO error: {e}")
        
        # Store in resources table
        if db.is_connected:
            resource_id = str(uuid.uuid4())
            await self.resource_repo.create(resource_id, project_id, 'bucket', name, {})
        
        await self._log_audit("CreateBucket", "bucket", name)
        
        return {
            "name": name,
            "project_id": project_id,
            "status": "ACTIVE",
            "endpoint": f"http://minio:9000/{name}",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_buckets(self, project_id: str) -> List[Dict]:
        buckets = []
        
        if storage.is_connected:
            try:
                for bucket in storage.client.list_buckets():
                    objects = list(storage.client.list_objects(bucket.name))
                    buckets.append({
                        "name": bucket.name,
                        "created_at": bucket.creation_date.isoformat() if bucket.creation_date else datetime.utcnow().isoformat(),
                        "object_count": len(objects),
                        "size_bytes": sum(obj.size or 0 for obj in objects) if objects else 0
                    })
            except Exception as e:
                print(f"MinIO list error: {e}")
        
        return buckets
    
    async def delete_bucket(self, project_id: str, bucket_name: str) -> Dict:
        from minio.error import S3Error
        
        if storage.is_connected:
            try:
                # Remove all objects first
                objects = storage.client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    storage.client.remove_object(bucket_name, obj.object_name)
                storage.client.remove_bucket(bucket_name)
            except S3Error as e:
                raise ValueError(f"MinIO error: {e}")
        
        # Remove from resources
        if db.is_connected:
            await db.execute(
                "DELETE FROM resources WHERE type = 'bucket' AND name = $1 AND project_id = $2",
                bucket_name, project_id
            )
        
        await self._log_audit("DeleteBucket", "bucket", bucket_name)
        return {"name": bucket_name, "status": "DELETED"}


class FunctionService(BaseService):
    """Business logic for serverless functions"""
    
    def __init__(self):
        self.resource_repo = RepositoryFactory.get_resource_repo()
    
    async def create(self, project_id: str, name: str, runtime: str = "python3.10",
                    memory_mb: int = 128, timeout_seconds: int = 30) -> Dict:
        function_id = str(uuid.uuid4())
        spec = {
            "runtime": runtime,
            "memory_mb": memory_mb,
            "timeout_seconds": timeout_seconds,
            "handler": "main.handler"
        }
        
        try:
            if db.is_connected:
                await self.resource_repo.create(
                    function_id, project_id, 'function', name, spec,
                    state={"status": "ACTIVE", "invocation_count": 0}
                )
                print(f"✅ Function created: {name} (ID: {function_id})")
            else:
                print(f"⚠️ Database not connected, function not persisted: {name}")
        except Exception as e:
            print(f"❌ Error creating function: {e}")
            raise
        
        await self._log_audit("CreateFunction", "function", function_id)
        
        return {
            "id": function_id,
            "name": name,
            "spec": spec,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        try:
            if db.is_connected:
                result = await self.resource_repo.list_by_project(project_id, "function")
                print(f"📋 Listed {len(result)} functions for project {project_id}")
                return result
            else:
                print(f"⚠️ Database not connected, returning empty list")
                return []
        except Exception as e:
            print(f"❌ Error listing functions: {e}")
            return []
    
    async def delete(self, project_id: str, function_id: str) -> Dict:
        try:
            if db.is_connected:
                await self.resource_repo.delete(project_id, function_id)
                print(f"🗑️ Function deleted: {function_id}")
        except Exception as e:
            print(f"❌ Error deleting function: {e}")
        
        await self._log_audit("DeleteFunction", "function", function_id)
        return {"id": function_id, "status": "DELETED"}
    
    async def invoke(self, function_id: str, payload: Dict = None) -> Dict:
        # Update invocation count
        try:
            if db.is_connected:
                await self.resource_repo.update_state(function_id, "invocation_count")
        except Exception as e:
            print(f"⚠️ Could not update invocation count: {e}")
        
        await self._log_audit("InvokeFunction", "function", function_id)
        
        return {
            "function_id": function_id,
            "status": "SUCCESS",
            "response": {"message": "Function executed", "input": payload or {}},
            "duration_ms": 42
        }


class WorkflowService(BaseService):
    """Business logic for durable workflows"""
    
    def __init__(self):
        self.resource_repo = RepositoryFactory.get_resource_repo()
        self.run_repo = RepositoryFactory.get_workflow_run_repo()
    
    async def create(self, project_id: str, name: str, definition: Dict = None) -> Dict:
        workflow_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.resource_repo.create(
                workflow_id, project_id, 'workflow', name, definition or {},
                state={"status": "ACTIVE", "run_count": 0}
            )
        
        await self._log_audit("CreateWorkflow", "workflow", workflow_id)
        
        return {
            "id": workflow_id,
            "name": name,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        return await self.resource_repo.list_by_project(project_id, "workflow")
    
    async def delete(self, project_id: str, workflow_id: str) -> Dict:
        if db.is_connected:
            await self.resource_repo.delete(project_id, workflow_id)
        
        await self._log_audit("DeleteWorkflow", "workflow", workflow_id)
        return {"id": workflow_id, "status": "DELETED"}
    
    async def start(self, workflow_name: str, input_data: Dict = None) -> Dict:
        run_id = str(uuid.uuid4())
        
        if db.is_connected:
            # Get workflow ID by name
            workflow = await db.fetchrow(
                "SELECT id FROM resources WHERE name = $1 AND type = 'workflow' LIMIT 1",
                workflow_name
            )
            workflow_id = workflow['id'] if workflow else None
            
            if workflow_id:
                await self.run_repo.create(run_id, workflow_id, workflow_name, input_data or {})
                await self.resource_repo.update_state(workflow_id, "run_count")
        
        await self._log_audit("StartWorkflow", "workflow", workflow_name)
        
        return {
            "workflow_name": workflow_name,
            "run_id": run_id,
            "status": "RUNNING",
            "started_at": datetime.utcnow().isoformat()
        }
    
    async def list_runs(self, workflow_name: str) -> List[Dict]:
        if db.is_connected:
            return await self.run_repo.list_by_workflow_name(workflow_name)
        return []


class EventRuleService(BaseService):
    """Business logic for event routing rules"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_event_rule_repo()
    
    async def create(self, project_id: str, name: str, description: str,
                    event_pattern: Dict, targets: List, enabled: bool = True) -> Dict:
        rule_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(rule_id, project_id, name, description, event_pattern, targets, enabled)
        
        await self._log_audit("CreateEventRule", "event_rule", rule_id)
        
        return {
            "id": rule_id,
            "name": name,
            "event_pattern": event_pattern,
            "targets": targets,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_project(project_id)
        return []
    
    async def delete(self, project_id: str, rule_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(project_id, rule_id)
        
        await self._log_audit("DeleteEventRule", "event_rule", rule_id)
        return {"id": rule_id, "status": "DELETED"}


class TopicService(BaseService):
    """Business logic for SNS-like topics"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_topic_repo()
        self.sub_repo = RepositoryFactory.get_subscription_repo()
    
    async def create(self, project_id: str, name: str, display_name: str = None,
                    description: str = None) -> Dict:
        topic_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(topic_id, project_id, name, display_name or name, description or "")
        
        await self._log_audit("CreateTopic", "topic", topic_id)
        
        return {
            "id": topic_id,
            "name": name,
            "arn": f"arn:minicloud:sns:{project_id}:{name}",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_project(project_id)
        return []
    
    async def delete(self, project_id: str, topic_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(project_id, topic_id)
        
        await self._log_audit("DeleteTopic", "topic", topic_id)
        return {"id": topic_id, "status": "DELETED"}
    
    async def publish(self, topic_id: str, body: str, attributes: Dict = None) -> Dict:
        delivered = 0
        
        if db.is_connected:
            await self.repo.increment_message_count(topic_id)
            
            # Get confirmed subscriptions
            subscriptions = await self.sub_repo.get_confirmed_by_topic(topic_id)
            
            for sub in subscriptions:
                await self.sub_repo.increment_delivery_count(sub['id'])
                delivered += 1
        
        await self._log_audit("PublishMessage", "topic", topic_id)
        
        return {
            "message_id": str(uuid.uuid4()),
            "topic_id": topic_id,
            "delivered_to": delivered
        }


class SubscriptionService(BaseService):
    """Business logic for topic subscriptions"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_subscription_repo()
    
    async def create(self, topic_id: str, protocol: str, endpoint: str,
                    filter_policy: Dict = None) -> Dict:
        sub_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(sub_id, topic_id, protocol, endpoint, filter_policy or {})
        
        await self._log_audit("Subscribe", "subscription", sub_id)
        
        return {
            "id": sub_id,
            "topic_id": topic_id,
            "protocol": protocol,
            "endpoint": endpoint,
            "status": "CONFIRMED",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_topic(self, topic_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_topic(topic_id)
        return []
    
    async def delete(self, subscription_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(subscription_id)
        
        await self._log_audit("Unsubscribe", "subscription", subscription_id)
        return {"id": subscription_id, "status": "DELETED"}


class QueueService(BaseService):
    """Business logic for SQS-like queues"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_queue_repo()
        self.msg_repo = RepositoryFactory.get_message_repo()
    
    async def create(self, project_id: str, name: str, description: str = None,
                    visibility_timeout: int = 30, message_retention: int = 345600,
                    delay_seconds: int = 0) -> Dict:
        queue_id = str(uuid.uuid4())
        
        if db.is_connected:
            await self.repo.create(
                queue_id, project_id, name, description or "",
                visibility_timeout, message_retention, delay_seconds
            )
        
        await self._log_audit("CreateQueue", "queue", queue_id)
        
        return {
            "id": queue_id,
            "name": name,
            "url": f"https://sqs.minicloud.local/{project_id}/{name}",
            "arn": f"arn:minicloud:sqs:{project_id}:{name}",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_project(project_id)
        return []
    
    async def get(self, queue_id: str) -> Dict:
        if db.is_connected:
            queue = await self.repo.get_by_id(queue_id)
            if queue:
                msg_count = await db.fetchval(
                    "SELECT COUNT(*) FROM messages WHERE queue_id = $1 AND visible_at <= NOW()",
                    queue_id
                )
                queue['approximate_message_count'] = msg_count or 0
                return queue
        raise ValueError("Queue not found")
    
    async def delete(self, project_id: str, queue_id: str) -> Dict:
        if db.is_connected:
            await self.repo.delete(project_id, queue_id)
        
        await self._log_audit("DeleteQueue", "queue", queue_id)
        return {"id": queue_id, "status": "DELETED"}
    
    async def send_message(self, queue_id: str, body: str, attributes: Dict = None,
                          delay_seconds: int = 0) -> Dict:
        message_id = str(uuid.uuid4())
        visible_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        if db.is_connected:
            await self.msg_repo.create(message_id, queue_id, body, attributes or {}, visible_at)
            await self.repo.update_message_count(queue_id, 1)
        
        await self._log_audit("SendMessage", "queue", queue_id)
        
        return {
            "message_id": message_id,
            "queue_id": queue_id,
            "body": body,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def receive_messages(self, queue_id: str, max_messages: int = 1,
                              visibility_timeout: int = 30) -> Dict:
        messages = []
        
        if db.is_connected:
            rows = await self.msg_repo.receive(queue_id, max_messages)
            
            for row in rows:
                receipt_handle = str(uuid.uuid4())
                new_visible_at = datetime.utcnow() + timedelta(seconds=visibility_timeout)
                
                await self.msg_repo.mark_in_flight(row['id'], receipt_handle, new_visible_at)
                
                msg = dict(row)
                msg['receipt_handle'] = receipt_handle
                if 'attributes' in msg and isinstance(msg['attributes'], str):
                    msg['attributes'] = json.loads(msg['attributes'])
                messages.append(msg)
            
            if messages:
                await self.repo.update_receive_count(queue_id, len(messages))
        
        return {"messages": messages, "count": len(messages)}
    
    async def delete_message(self, queue_id: str, receipt_handle: str) -> Dict:
        if db.is_connected:
            await self.msg_repo.delete_by_receipt(queue_id, receipt_handle)
        
        await self._log_audit("DeleteMessage", "queue", queue_id)
        return {"queue_id": queue_id, "receipt_handle": receipt_handle, "status": "DELETED"}
    
    async def purge(self, queue_id: str) -> Dict:
        deleted = 0
        
        if db.is_connected:
            deleted = await self.msg_repo.delete_all_by_queue(queue_id)
            await db.execute("UPDATE queues SET message_count = 0 WHERE id = $1", queue_id)
        
        await self._log_audit("PurgeQueue", "queue", queue_id)
        return {"queue_id": queue_id, "deleted_count": deleted}


class AuditLogService(BaseService):
    """Business logic for audit logs"""
    
    def __init__(self):
        self.repo = RepositoryFactory.get_audit_repo()
    
    async def list_by_org(self, org_id: str, resource_type: str = None,
                         limit: int = 100) -> List[Dict]:
        if db.is_connected:
            return await self.repo.list_by_org(org_id, resource_type, limit)
        return []


class MetricsService(BaseService):
    """Business logic for metrics and usage"""
    
    async def get_usage(self, project_id: str) -> Dict:
        usage = {
            "storage_bytes": 0,
            "function_invocations": 0,
            "workflow_runs": 0,
            "api_calls_24h": 0
        }
        
        # Get storage from MinIO
        if storage.is_connected:
            try:
                for bucket in storage.client.list_buckets():
                    for obj in storage.client.list_objects(bucket.name, recursive=True):
                        usage["storage_bytes"] += obj.size or 0
            except:
                pass
        
        # Get counts from database
        if db.is_connected:
            try:
                row = await db.fetchrow("""
                    SELECT 
                        COALESCE(SUM((state::jsonb->>'invocation_count')::int), 0) as fn_invocations,
                        COALESCE(SUM((state::jsonb->>'run_count')::int), 0) as wf_runs
                    FROM resources WHERE project_id = $1
                """, project_id)
                
                if row:
                    usage["function_invocations"] = row['fn_invocations'] or 0
                    usage["workflow_runs"] = row['wf_runs'] or 0
                
                count = await db.fetchval(
                    "SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '24 hours'"
                )
                usage["api_calls_24h"] = count or 0
            except:
                pass
        
        return {"project_id": project_id, "period": "current", **usage}
    
    async def get_resource_counts(self) -> Dict:
        """Get counts for Prometheus metrics"""
        counts = {
            "functions": 0,
            "workflows": 0,
            "buckets": 0,
            "topics": 0,
            "queues": 0
        }
        
        if db.is_connected:
            # Query each table separately to handle missing tables
            try:
                counts["functions"] = await db.fetchval(
                    "SELECT COUNT(*) FROM resources WHERE type = 'function'"
                ) or 0
            except:
                pass
            
            try:
                counts["workflows"] = await db.fetchval(
                    "SELECT COUNT(*) FROM resources WHERE type = 'workflow'"
                ) or 0
            except:
                pass
            
            try:
                counts["buckets"] = await db.fetchval(
                    "SELECT COUNT(*) FROM resources WHERE type = 'bucket'"
                ) or 0
            except:
                pass
            
            try:
                counts["topics"] = await db.fetchval("SELECT COUNT(*) FROM topics") or 0
            except:
                pass
            
            try:
                counts["queues"] = await db.fetchval("SELECT COUNT(*) FROM queues") or 0
            except:
                pass
        
        return counts


# Service factory - Dependency Inversion Principle
class ServiceFactory:
    """Factory for creating service instances"""
    
    _instances = {}
    
    @classmethod
    def get_organization_service(cls) -> OrganizationService:
        if 'org' not in cls._instances:
            cls._instances['org'] = OrganizationService()
        return cls._instances['org']
    
    @classmethod
    def get_project_service(cls) -> ProjectService:
        if 'project' not in cls._instances:
            cls._instances['project'] = ProjectService()
        return cls._instances['project']
    
    @classmethod
    def get_user_service(cls) -> UserService:
        if 'user' not in cls._instances:
            cls._instances['user'] = UserService()
        return cls._instances['user']
    
    @classmethod
    def get_policy_service(cls) -> PolicyService:
        if 'policy' not in cls._instances:
            cls._instances['policy'] = PolicyService()
        return cls._instances['policy']
    
    @classmethod
    def get_resource_service(cls) -> ResourceService:
        if 'resource' not in cls._instances:
            cls._instances['resource'] = ResourceService()
        return cls._instances['resource']
    
    @classmethod
    def get_storage_service(cls) -> StorageService:
        if 'storage' not in cls._instances:
            cls._instances['storage'] = StorageService()
        return cls._instances['storage']
    
    @classmethod
    def get_function_service(cls) -> FunctionService:
        if 'function' not in cls._instances:
            cls._instances['function'] = FunctionService()
        return cls._instances['function']
    
    @classmethod
    def get_workflow_service(cls) -> WorkflowService:
        if 'workflow' not in cls._instances:
            cls._instances['workflow'] = WorkflowService()
        return cls._instances['workflow']
    
    @classmethod
    def get_event_rule_service(cls) -> EventRuleService:
        if 'event_rule' not in cls._instances:
            cls._instances['event_rule'] = EventRuleService()
        return cls._instances['event_rule']
    
    @classmethod
    def get_topic_service(cls) -> TopicService:
        if 'topic' not in cls._instances:
            cls._instances['topic'] = TopicService()
        return cls._instances['topic']
    
    @classmethod
    def get_subscription_service(cls) -> SubscriptionService:
        if 'subscription' not in cls._instances:
            cls._instances['subscription'] = SubscriptionService()
        return cls._instances['subscription']
    
    @classmethod
    def get_queue_service(cls) -> QueueService:
        if 'queue' not in cls._instances:
            cls._instances['queue'] = QueueService()
        return cls._instances['queue']
    
    @classmethod
    def get_audit_service(cls) -> AuditLogService:
        if 'audit' not in cls._instances:
            cls._instances['audit'] = AuditLogService()
        return cls._instances['audit']
    
    @classmethod
    def get_metrics_service(cls) -> MetricsService:
        if 'metrics' not in cls._instances:
            cls._instances['metrics'] = MetricsService()
        return cls._instances['metrics']
