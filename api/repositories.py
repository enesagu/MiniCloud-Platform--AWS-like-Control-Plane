"""
MiniCloud Platform - Repository Layer
Data Access Objects following Single Responsibility Principle
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from .database import db


class BaseRepository(ABC):
    """Abstract base repository - Dependency Inversion Principle"""
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        pass


class OrganizationRepository(BaseRepository):
    """Data access for organizations"""
    
    @property
    def table_name(self) -> str:
        return "organizations"
    
    async def create(self, org_id: str, name: str, display_name: str) -> None:
        await db.execute(
            "INSERT INTO organizations (id, name, display_name, created_at) VALUES ($1, $2, $3, $4)",
            org_id, name, display_name, datetime.utcnow()
        )
    
    async def list_all(self) -> List[Dict]:
        rows = await db.fetch("SELECT * FROM organizations ORDER BY created_at DESC")
        return [dict(r) for r in rows] if rows else []
    
    async def get_by_id(self, org_id: str) -> Optional[Dict]:
        row = await db.fetchrow("SELECT * FROM organizations WHERE id = $1", org_id)
        return dict(row) if row else None


class ProjectRepository(BaseRepository):
    """Data access for projects"""
    
    @property
    def table_name(self) -> str:
        return "projects"
    
    async def create(self, project_id: str, org_id: str, name: str, display_name: str) -> None:
        await db.execute(
            "INSERT INTO projects (id, org_id, name, display_name, created_at) VALUES ($1, $2, $3, $4, $5)",
            project_id, org_id, name, display_name, datetime.utcnow()
        )
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        rows = await db.fetch("SELECT * FROM projects WHERE org_id = $1 ORDER BY created_at DESC", org_id)
        return [dict(r) for r in rows] if rows else []


class UserRepository(BaseRepository):
    """Data access for users"""
    
    @property
    def table_name(self) -> str:
        return "users"
    
    async def create(self, user_id: str, org_id: str, username: str, email: str, password_hash: str) -> None:
        await db.execute(
            "INSERT INTO users (id, org_id, username, email, password_hash, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            user_id, org_id, username, email, password_hash, datetime.utcnow()
        )
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT id, org_id, username, email, created_at FROM users WHERE org_id = $1", org_id
        )
        return [dict(r) for r in rows] if rows else []
    
    async def delete(self, org_id: str, user_id: str) -> None:
        await db.execute("DELETE FROM users WHERE id = $1 AND org_id = $2", user_id, org_id)


class PolicyRepository(BaseRepository):
    """Data access for policies"""
    
    @property
    def table_name(self) -> str:
        return "policies"
    
    async def create(self, policy_id: str, org_id: str, name: str, description: str, document: Dict) -> None:
        await db.execute(
            "INSERT INTO policies (id, org_id, name, description, document, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            policy_id, org_id, name, description, json.dumps(document), datetime.utcnow()
        )
    
    async def list_by_org(self, org_id: str) -> List[Dict]:
        rows = await db.fetch("SELECT * FROM policies WHERE org_id = $1", org_id)
        result = []
        for r in rows:
            d = dict(r)
            if 'document' in d and isinstance(d['document'], str):
                d['document'] = json.loads(d['document'])
            result.append(d)
        return result


class ResourceRepository(BaseRepository):
    """Data access for generic resources"""
    
    @property
    def table_name(self) -> str:
        return "resources"
    
    async def create(self, resource_id: str, project_id: str, resource_type: str, 
                    name: str, spec: Dict, state: Dict = None, tags: Dict = None) -> None:
        await db.execute(
            """INSERT INTO resources (id, project_id, type, name, spec, state, tags, created_at) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            resource_id, project_id, resource_type, name, 
            json.dumps(spec), json.dumps(state or {"status": "ACTIVE"}), 
            json.dumps(tags or {}), datetime.utcnow()
        )
    
    async def list_by_project(self, project_id: str, resource_type: str = None) -> List[Dict]:
        if resource_type:
            rows = await db.fetch(
                "SELECT * FROM resources WHERE project_id = $1 AND type = $2 ORDER BY created_at DESC",
                project_id, resource_type
            )
        else:
            rows = await db.fetch(
                "SELECT * FROM resources WHERE project_id = $1 ORDER BY created_at DESC",
                project_id
            )
        
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
    
    async def get_by_id(self, project_id: str, resource_id: str) -> Optional[Dict]:
        row = await db.fetchrow(
            "SELECT * FROM resources WHERE id = $1 AND project_id = $2", resource_id, project_id
        )
        return dict(row) if row else None
    
    async def delete(self, project_id: str, resource_id: str) -> None:
        await db.execute("DELETE FROM resources WHERE id = $1 AND project_id = $2", resource_id, project_id)
    
    async def update_state(self, resource_id: str, state_key: str, increment: int = 1) -> None:
        await db.execute(
            f"""UPDATE resources SET state = jsonb_set(
                COALESCE(state::jsonb, '{{}}'), 
                '{{{state_key}}}', 
                (COALESCE((state::jsonb->>'{state_key}')::int, 0) + {increment})::text::jsonb
            ) WHERE id = $1""",
            resource_id
        )


class EventRuleRepository(BaseRepository):
    """Data access for event rules"""
    
    @property
    def table_name(self) -> str:
        return "event_rules"
    
    async def create(self, rule_id: str, project_id: str, name: str, 
                    description: str, event_pattern: Dict, targets: List, enabled: bool) -> None:
        await db.execute(
            """INSERT INTO event_rules (id, project_id, name, description, event_pattern, targets, enabled, created_at) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            rule_id, project_id, name, description, 
            json.dumps(event_pattern), json.dumps(targets), enabled, datetime.utcnow()
        )
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT * FROM event_rules WHERE project_id = $1 ORDER BY created_at DESC", project_id
        )
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
    
    async def delete(self, project_id: str, rule_id: str) -> None:
        await db.execute("DELETE FROM event_rules WHERE id = $1 AND project_id = $2", rule_id, project_id)


class TopicRepository(BaseRepository):
    """Data access for SNS-like topics"""
    
    @property
    def table_name(self) -> str:
        return "topics"
    
    async def create(self, topic_id: str, project_id: str, name: str, 
                    display_name: str, description: str) -> None:
        await db.execute(
            "INSERT INTO topics (id, project_id, name, display_name, description, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            topic_id, project_id, name, display_name, description, datetime.utcnow()
        )
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT * FROM topics WHERE project_id = $1 ORDER BY created_at DESC", project_id
        )
        return [dict(r) for r in rows] if rows else []
    
    async def delete(self, project_id: str, topic_id: str) -> None:
        await db.execute("DELETE FROM topics WHERE id = $1 AND project_id = $2", topic_id, project_id)
    
    async def increment_message_count(self, topic_id: str) -> None:
        await db.execute("UPDATE topics SET message_count = message_count + 1 WHERE id = $1", topic_id)


class SubscriptionRepository(BaseRepository):
    """Data access for topic subscriptions"""
    
    @property
    def table_name(self) -> str:
        return "subscriptions"
    
    async def create(self, sub_id: str, topic_id: str, protocol: str, 
                    endpoint: str, filter_policy: Dict) -> None:
        await db.execute(
            "INSERT INTO subscriptions (id, topic_id, protocol, endpoint, filter_policy, status, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            sub_id, topic_id, protocol, endpoint, json.dumps(filter_policy), 'CONFIRMED', datetime.utcnow()
        )
    
    async def list_by_topic(self, topic_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT * FROM subscriptions WHERE topic_id = $1 ORDER BY created_at DESC", topic_id
        )
        return [dict(r) for r in rows] if rows else []
    
    async def get_confirmed_by_topic(self, topic_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT * FROM subscriptions WHERE topic_id = $1 AND status = 'CONFIRMED'", topic_id
        )
        return [dict(r) for r in rows] if rows else []
    
    async def delete(self, sub_id: str) -> None:
        await db.execute("DELETE FROM subscriptions WHERE id = $1", sub_id)
    
    async def increment_delivery_count(self, sub_id: str) -> None:
        await db.execute("UPDATE subscriptions SET delivery_count = delivery_count + 1 WHERE id = $1", sub_id)


class QueueRepository(BaseRepository):
    """Data access for SQS-like queues"""
    
    @property
    def table_name(self) -> str:
        return "queues"
    
    async def create(self, queue_id: str, project_id: str, name: str, description: str,
                    visibility_timeout: int, message_retention: int, delay_seconds: int) -> None:
        await db.execute(
            """INSERT INTO queues (id, project_id, name, description, visibility_timeout, message_retention, delay_seconds, created_at) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            queue_id, project_id, name, description, visibility_timeout, message_retention, delay_seconds, datetime.utcnow()
        )
    
    async def list_by_project(self, project_id: str) -> List[Dict]:
        rows = await db.fetch(
            "SELECT * FROM queues WHERE project_id = $1 ORDER BY created_at DESC", project_id
        )
        return [dict(r) for r in rows] if rows else []
    
    async def get_by_id(self, queue_id: str) -> Optional[Dict]:
        row = await db.fetchrow("SELECT * FROM queues WHERE id = $1", queue_id)
        return dict(row) if row else None
    
    async def delete(self, project_id: str, queue_id: str) -> None:
        await db.execute("DELETE FROM queues WHERE id = $1 AND project_id = $2", queue_id, project_id)
    
    async def update_message_count(self, queue_id: str, increment: int) -> None:
        await db.execute(
            "UPDATE queues SET message_count = message_count + $1 WHERE id = $2", increment, queue_id
        )
    
    async def update_receive_count(self, queue_id: str, increment: int) -> None:
        await db.execute(
            "UPDATE queues SET receive_count = receive_count + $1 WHERE id = $2", increment, queue_id
        )


class MessageRepository(BaseRepository):
    """Data access for queue messages"""
    
    @property
    def table_name(self) -> str:
        return "messages"
    
    async def create(self, message_id: str, queue_id: str, body: str, 
                    attributes: Dict, visible_at: datetime) -> None:
        await db.execute(
            """INSERT INTO messages (id, queue_id, body, attributes, visible_at, sent_at) 
               VALUES ($1, $2, $3, $4, $5, $6)""",
            message_id, queue_id, body, json.dumps(attributes), visible_at, datetime.utcnow()
        )
    
    async def receive(self, queue_id: str, max_messages: int) -> List[Dict]:
        rows = await db.fetch(
            """SELECT * FROM messages 
               WHERE queue_id = $1 AND visible_at <= NOW() AND receipt_handle IS NULL
               ORDER BY sent_at LIMIT $2""",
            queue_id, max_messages
        )
        return [dict(r) for r in rows] if rows else []
    
    async def mark_in_flight(self, message_id: str, receipt_handle: str, visible_at: datetime) -> None:
        await db.execute(
            """UPDATE messages SET receipt_handle = $1, visible_at = $2, 
               receive_count = receive_count + 1, first_received_at = COALESCE(first_received_at, NOW())
               WHERE id = $3""",
            receipt_handle, visible_at, message_id
        )
    
    async def delete_by_receipt(self, queue_id: str, receipt_handle: str) -> None:
        await db.execute(
            "DELETE FROM messages WHERE queue_id = $1 AND receipt_handle = $2",
            queue_id, receipt_handle
        )
    
    async def delete_all_by_queue(self, queue_id: str) -> int:
        count = await db.fetchval("SELECT COUNT(*) FROM messages WHERE queue_id = $1", queue_id)
        await db.execute("DELETE FROM messages WHERE queue_id = $1", queue_id)
        return count or 0


class AuditLogRepository(BaseRepository):
    """Data access for audit logs"""
    
    @property
    def table_name(self) -> str:
        return "audit_logs"
    
    async def create(self, action: str, resource_type: str, resource_id: str, 
                    actor_id: str = "system", org_id: str = "org-default",
                    project_id: str = "proj-default", details: str = None) -> None:
        await db.execute(
            """INSERT INTO audit_logs (id, org_id, project_id, actor_id, action, resource_type, resource_id, details, ip_address, timestamp)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            str(uuid.uuid4()), org_id, project_id, actor_id, action, 
            resource_type, resource_id, details, '127.0.0.1', datetime.utcnow()
        )
    
    async def list_by_org(self, org_id: str, resource_type: str = None, limit: int = 100) -> List[Dict]:
        if resource_type:
            rows = await db.fetch(
                "SELECT * FROM audit_logs WHERE org_id = $1 AND resource_type = $2 ORDER BY timestamp DESC LIMIT $3",
                org_id, resource_type, limit
            )
        else:
            rows = await db.fetch(
                "SELECT * FROM audit_logs WHERE org_id = $1 ORDER BY timestamp DESC LIMIT $2",
                org_id, limit
            )
        return [dict(r) for r in rows] if rows else []


class WorkflowRunRepository(BaseRepository):
    """Data access for workflow runs"""
    
    @property
    def table_name(self) -> str:
        return "workflow_runs"
    
    async def create(self, run_id: str, workflow_id: str, workflow_name: str, input_data: Dict) -> None:
        await db.execute(
            "INSERT INTO workflow_runs (id, workflow_id, workflow_name, status, input, started_at) VALUES ($1, $2, $3, $4, $5, $6)",
            run_id, workflow_id, workflow_name, 'RUNNING', json.dumps(input_data), datetime.utcnow()
        )
    
    async def list_by_workflow_name(self, workflow_name: str, limit: int = 50) -> List[Dict]:
        rows = await db.fetch(
            """SELECT wr.* FROM workflow_runs wr
               JOIN resources r ON wr.workflow_id = r.id
               WHERE r.name = $1 AND r.type = 'workflow'
               ORDER BY wr.started_at DESC LIMIT $2""",
            workflow_name, limit
        )
        return [dict(r) for r in rows] if rows else []


# Repository factory - Dependency Inversion
class RepositoryFactory:
    """Factory for creating repository instances"""
    
    _instances = {}
    
    @classmethod
    def get_organization_repo(cls) -> OrganizationRepository:
        if 'org' not in cls._instances:
            cls._instances['org'] = OrganizationRepository()
        return cls._instances['org']
    
    @classmethod
    def get_project_repo(cls) -> ProjectRepository:
        if 'project' not in cls._instances:
            cls._instances['project'] = ProjectRepository()
        return cls._instances['project']
    
    @classmethod
    def get_user_repo(cls) -> UserRepository:
        if 'user' not in cls._instances:
            cls._instances['user'] = UserRepository()
        return cls._instances['user']
    
    @classmethod
    def get_policy_repo(cls) -> PolicyRepository:
        if 'policy' not in cls._instances:
            cls._instances['policy'] = PolicyRepository()
        return cls._instances['policy']
    
    @classmethod
    def get_resource_repo(cls) -> ResourceRepository:
        if 'resource' not in cls._instances:
            cls._instances['resource'] = ResourceRepository()
        return cls._instances['resource']
    
    @classmethod
    def get_event_rule_repo(cls) -> EventRuleRepository:
        if 'event_rule' not in cls._instances:
            cls._instances['event_rule'] = EventRuleRepository()
        return cls._instances['event_rule']
    
    @classmethod
    def get_topic_repo(cls) -> TopicRepository:
        if 'topic' not in cls._instances:
            cls._instances['topic'] = TopicRepository()
        return cls._instances['topic']
    
    @classmethod
    def get_subscription_repo(cls) -> SubscriptionRepository:
        if 'subscription' not in cls._instances:
            cls._instances['subscription'] = SubscriptionRepository()
        return cls._instances['subscription']
    
    @classmethod
    def get_queue_repo(cls) -> QueueRepository:
        if 'queue' not in cls._instances:
            cls._instances['queue'] = QueueRepository()
        return cls._instances['queue']
    
    @classmethod
    def get_message_repo(cls) -> MessageRepository:
        if 'message' not in cls._instances:
            cls._instances['message'] = MessageRepository()
        return cls._instances['message']
    
    @classmethod
    def get_audit_repo(cls) -> AuditLogRepository:
        if 'audit' not in cls._instances:
            cls._instances['audit'] = AuditLogRepository()
        return cls._instances['audit']
    
    @classmethod
    def get_workflow_run_repo(cls) -> WorkflowRunRepository:
        if 'workflow_run' not in cls._instances:
            cls._instances['workflow_run'] = WorkflowRunRepository()
        return cls._instances['workflow_run']
