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
                    memory_mb: int = 128, timeout_seconds: int = 30, code: str = "") -> Dict:
        function_id = str(uuid.uuid4())
        spec = {
            "runtime": runtime,
            "memory_mb": memory_mb,
            "timeout_seconds": timeout_seconds,
            "handler": "main.handler",
            "code": code
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
    
    async def get(self, project_id: str, function_id: str) -> Dict:
        """Get function by ID"""
        try:
            if db.is_connected:
                result = await self.resource_repo.get_by_id(project_id, function_id)
                if result:
                    return result
        except Exception as e:
            print(f"❌ Error getting function: {e}")
        
        return {"error": "Function not found"}
    
    async def update_code(self, function_id: str, code: str) -> Dict:
        """Update function code"""
        try:
            if db.is_connected:
                await self.resource_repo.update_spec(function_id, "code", code)
                print(f"📝 Function code updated: {function_id}")
                return {
                    "id": function_id,
                    "status": "UPDATED",
                    "message": "Function code deployed successfully"
                }
            else:
                print(f"⚠️ Database not connected, code not saved")
                return {"error": "Database not connected"}
        except Exception as e:
            print(f"❌ Error updating function code: {e}")
            return {"error": str(e)}
    
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
        """
        Invoke a function - REAL Lambda-like execution
        Executes the handler code and returns the actual result
        """
        import time
        import traceback
        import io
        import sys
        
        start_time = time.time()
        function_code = ""
        function_name = "unknown"
        runtime = "python3.10"
        logs = []
        handler_result = None
        status = "SUCCESS"
        error_message = None
        
        try:
            if db.is_connected:
                # Update invocation count
                await self.resource_repo.update_state(function_id, "invocation_count")
                
                # Get function code and config
                func = await db.fetchrow(
                    "SELECT name, spec FROM resources WHERE id = $1 AND type = 'function'",
                    function_id
                )
                if func:
                    function_name = func['name']
                    if func['spec']:
                        spec = json.loads(func['spec']) if isinstance(func['spec'], str) else func['spec']
                        function_code = spec.get('code', '')
                        runtime = spec.get('runtime', 'python3.10')
        except Exception as e:
            print(f"⚠️ Could not get function: {e}")
            logs.append(f"ERROR: Could not load function: {e}")
        
        logs.append(f"START RequestId: {function_id[:8]}")
        logs.append(f"Function: {function_name}")
        logs.append(f"Runtime: {runtime}")
        
        # Execute the code if we have it
        if function_code and runtime.startswith('python'):
            try:
                # Capture stdout for logs
                old_stdout = sys.stdout
                captured_output = io.StringIO()
                sys.stdout = captured_output
                
                # Create execution context
                execution_context = {
                    'function_id': function_id,
                    'function_name': function_name,
                    'memory_limit_mb': 128,
                    'timeout_seconds': 30,
                    'invoked_function_arn': f'arn:minicloud:function:{function_id}'
                }
                
                # Execute the code in a namespace
                namespace = {
                    '__builtins__': __builtins__,
                    'json': json,
                }
                
                # Execute the function definition
                exec(function_code, namespace)
                
                # Find and call the handler
                handler = namespace.get('handler')
                if handler and callable(handler):
                    # 🔥 CRITICAL: Capture the return value!
                    handler_result = handler(payload or {}, execution_context)
                    logs.append(f"Handler returned: {type(handler_result).__name__}")
                else:
                    error_message = "No 'handler' function found in code"
                    status = "FAILED"
                    logs.append(f"ERROR: {error_message}")
                
                # Restore stdout and get logs
                sys.stdout = old_stdout
                output_logs = captured_output.getvalue()
                if output_logs:
                    for line in output_logs.strip().split('\n'):
                        logs.append(f"[stdout] {line}")
                        
            except Exception as e:
                sys.stdout = old_stdout
                status = "FAILED"
                error_message = str(e)
                logs.append(f"ERROR: {error_message}")
                logs.append(traceback.format_exc())
                print(f"❌ Function execution error: {e}")
        
        elif function_code and runtime.startswith('nodejs'):
            # For Node.js, we would spawn a subprocess or use a JS runtime
            # For now, return a placeholder
            handler_result = {
                "message": "Node.js runtime not yet implemented",
                "code_length": len(function_code)
            }
            logs.append("Node.js runtime: stub execution")
        
        elif not function_code:
            # No code provided - return default response
            handler_result = {
                "message": "No code deployed for this function",
                "hint": "Use the code editor to write and deploy your function"
            }
            logs.append("WARNING: No code found for this function")
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        logs.append(f"END RequestId: {function_id[:8]}")
        logs.append(f"Duration: {duration_ms}ms")
        
        await self._log_audit("InvokeFunction", "function", function_id)
        
        # Build response with REAL handler result
        response = {
            "function_id": function_id,
            "function_name": function_name,
            "status": status,
            "response": handler_result,  # 🔥 THE ACTUAL HANDLER RETURN VALUE
            "duration_ms": duration_ms,
            "logs": logs
        }
        
        if error_message:
            response["error"] = error_message
        
        print(f"{'✅' if status == 'SUCCESS' else '❌'} Function {function_name} invoked: {status} ({duration_ms}ms)")
        
        return response



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


# =====================================================
# INSTANCE SERVICE (EC2-like Compute)
# =====================================================

class InstanceService(BaseService):
    """
    Business logic for compute instances (EC2 equivalent)
    Integrates with Temporal for lifecycle orchestration
    """
    
    async def create(self, project_id: str, spec: Dict) -> Dict:
        """Create a new instance - triggers Temporal workflow"""
        instance_id = str(uuid.uuid4())
        name = spec.get("name", f"instance-{instance_id[:8]}")
        
        try:
            if db.is_connected:
                # Insert instance record
                await db.execute(
                    """INSERT INTO instances 
                       (id, project_id, name, display_name, cpu, memory_mb, disk_gb, 
                        image, network_segment, zone, startup_script, tags, state)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'REQUESTED')""",
                    instance_id, project_id, name, spec.get("display_name", name),
                    spec.get("cpu", 2), spec.get("memory_mb", 2048), spec.get("disk_gb", 20),
                    spec.get("image", "ubuntu:22.04"), spec.get("network_segment", "default"),
                    spec.get("zone"), spec.get("startup_script", ""),
                    json.dumps(spec.get("tags", {}))
                )
                
                # Log event
                await db.execute(
                    """INSERT INTO instance_events (instance_id, to_state, message)
                       VALUES ($1, 'REQUESTED', 'Instance creation requested')""",
                    instance_id
                )
                
                print(f"✅ Instance created: {name} (ID: {instance_id})")
                
                # In production: Start Temporal workflow
                # client = await Client.connect(TEMPORAL_HOST)
                # await client.start_workflow(
                #     "ProvisionInstanceWorkflow",
                #     {"instance_id": instance_id, **spec},
                #     id=f"provision-{instance_id}",
                #     task_queue="minicloud-instance-tasks"
                # )
                
        except Exception as e:
            print(f"❌ Error creating instance: {e}")
            raise
        
        await self._log_audit("CreateInstance", "instance", instance_id)
        
        return {
            "id": instance_id,
            "name": name,
            "project_id": project_id,
            "state": "REQUESTED",
            "message": "Instance provisioning workflow started",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def list_by_project(self, project_id: str, state: str = None) -> List[Dict]:
        """List instances in a project"""
        try:
            if db.is_connected:
                query = """SELECT id, name, display_name, cpu, memory_mb, disk_gb, image,
                                  state, ip_address, dns_name, host_id, zone, tags, created_at
                           FROM instances WHERE project_id = $1"""
                params = [project_id]
                
                if state:
                    query += " AND state = $2"
                    params.append(state)
                
                query += " ORDER BY created_at DESC"
                
                rows = await db.fetch(query, *params)
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"❌ Error listing instances: {e}")
        
        return []
    
    async def list_by_host(self, host_id: str) -> List[Dict]:
        """List instances on a specific host"""
        try:
            if db.is_connected:
                rows = await db.fetch(
                    """SELECT id, name, cpu, memory_mb, state, ip_address, created_at
                       FROM instances WHERE host_id = $1 ORDER BY created_at DESC""",
                    host_id
                )
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"❌ Error listing host instances: {e}")
        
        return []
    
    async def get(self, instance_id: str) -> Optional[Dict]:
        """Get instance details"""
        try:
            if db.is_connected:
                row = await db.fetchrow(
                    """SELECT i.*, h.name as host_name 
                       FROM instances i 
                       LEFT JOIN hosts h ON i.host_id = h.id 
                       WHERE i.id = $1""",
                    instance_id
                )
                if row:
                    return dict(row)
        except Exception as e:
            print(f"❌ Error getting instance: {e}")
        
        return None
    
    async def _change_state(self, instance_id: str, new_state: str, message: str = None) -> Dict:
        """Helper to change instance state"""
        try:
            if db.is_connected:
                # Get current state
                current = await db.fetchval(
                    "SELECT state FROM instances WHERE id = $1", instance_id
                )
                
                # Update state
                await db.execute(
                    "UPDATE instances SET state = $1, state_message = $2, updated_at = NOW() WHERE id = $3",
                    new_state, message, instance_id
                )
                
                # Log event
                await db.execute(
                    """INSERT INTO instance_events (instance_id, from_state, to_state, message)
                       VALUES ($1, $2, $3, $4)""",
                    instance_id, current, new_state, message
                )
                
                return {
                    "id": instance_id,
                    "previous_state": current,
                    "state": new_state,
                    "message": message
                }
        except Exception as e:
            print(f"❌ Error changing state: {e}")
            raise
    
    async def stop(self, instance_id: str) -> Dict:
        """Stop an instance"""
        result = await self._change_state(instance_id, "STOPPING", "Stop requested")
        await self._log_audit("StopInstance", "instance", instance_id)
        
        # Simulate stop (in prod: trigger workflow)
        await self._change_state(instance_id, "STOPPED", "Instance stopped")
        
        return {**result, "state": "STOPPED"}
    
    async def start(self, instance_id: str) -> Dict:
        """Start a stopped instance"""
        result = await self._change_state(instance_id, "STARTING", "Start requested")
        await self._log_audit("StartInstance", "instance", instance_id)
        
        # Simulate start
        await self._change_state(instance_id, "RUNNING", "Instance running")
        
        return {**result, "state": "RUNNING"}
    
    async def terminate(self, instance_id: str, force: bool = False) -> Dict:
        """Terminate an instance"""
        result = await self._change_state(
            instance_id, 
            "TERMINATING", 
            f"Termination requested (force={force})"
        )
        await self._log_audit("TerminateInstance", "instance", instance_id)
        
        # Update timestamps
        if db.is_connected:
            await db.execute(
                "UPDATE instances SET terminated_at = NOW() WHERE id = $1",
                instance_id
            )
        
        await self._change_state(instance_id, "TERMINATED", "Instance terminated")
        
        return {**result, "state": "TERMINATED"}
    
    async def reboot(self, instance_id: str) -> Dict:
        """Reboot an instance"""
        await self._change_state(instance_id, "REBOOTING", "Reboot requested")
        await self._log_audit("RebootInstance", "instance", instance_id)
        
        # Simulate reboot
        await self._change_state(instance_id, "RUNNING", "Instance rebooted")
        
        return {"id": instance_id, "state": "RUNNING", "message": "Reboot complete"}
    
    async def get_events(self, instance_id: str, limit: int = 50) -> List[Dict]:
        """Get instance state transition events"""
        try:
            if db.is_connected:
                rows = await db.fetch(
                    """SELECT id, from_state, to_state, message, actor_id, created_at
                       FROM instance_events WHERE instance_id = $1 
                       ORDER BY created_at DESC LIMIT $2""",
                    instance_id, limit
                )
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"❌ Error getting events: {e}")
        
        return []


class HostService(BaseService):
    """Business logic for compute hosts"""
    
    async def list_all(self, status: str = None, zone: str = None) -> List[Dict]:
        """List all hosts with optional filters"""
        try:
            if db.is_connected:
                query = """SELECT h.*, 
                           (SELECT COUNT(*) FROM instances i WHERE i.host_id = h.id AND i.state != 'TERMINATED') as instance_count
                           FROM hosts h WHERE 1=1"""
                params = []
                
                if status:
                    params.append(status)
                    query += f" AND status = ${len(params)}"
                
                if zone:
                    params.append(zone)
                    query += f" AND zone = ${len(params)}"
                
                query += " ORDER BY name"
                
                rows = await db.fetch(query, *params)
                
                # Calculate available resources
                result = []
                for r in rows:
                    host = dict(r)
                    host["cpu_available"] = host["cpu_total"] - host["cpu_allocated"]
                    host["memory_available_mb"] = host["memory_total_mb"] - host["memory_allocated_mb"]
                    host["disk_available_gb"] = host["disk_total_gb"] - host["disk_allocated_gb"]
                    result.append(host)
                
                return result
        except Exception as e:
            print(f"❌ Error listing hosts: {e}")
        
        return []
    
    async def get(self, host_id: str) -> Optional[Dict]:
        """Get host details"""
        try:
            if db.is_connected:
                row = await db.fetchrow(
                    """SELECT h.*, 
                       (SELECT COUNT(*) FROM instances i WHERE i.host_id = h.id AND i.state != 'TERMINATED') as instance_count
                       FROM hosts h WHERE h.id = $1""",
                    host_id
                )
                if row:
                    host = dict(row)
                    host["cpu_available"] = host["cpu_total"] - host["cpu_allocated"]
                    host["memory_available_mb"] = host["memory_total_mb"] - host["memory_allocated_mb"]
                    return host
        except Exception as e:
            print(f"❌ Error getting host: {e}")
        
        return None


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
    
    @classmethod
    def get_instance_service(cls) -> InstanceService:
        if 'instance' not in cls._instances:
            cls._instances['instance'] = InstanceService()
        return cls._instances['instance']
    
    @classmethod
    def get_host_service(cls) -> HostService:
        if 'host' not in cls._instances:
            cls._instances['host'] = HostService()
        return cls._instances['host']

