"""
MiniCloud Platform - Event Router
Listens to NATS events and routes them to appropriate targets (Temporal workflows, Functions).
This is the EventBridge equivalent.
"""

import asyncio
import json
import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import nats
from nats.aio.client import Client as NATS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("event-router")

# Configuration from environment
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/minicloud")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")


@dataclass
class EventRule:
    """Represents an event routing rule (EventBridge Rule equivalent)."""
    id: str
    name: str
    project_id: str
    event_pattern: Dict[str, Any]
    targets: List[Dict[str, Any]]
    enabled: bool = True


class EventMatcher:
    """Matches incoming events against event patterns."""
    
    def matches(self, event: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """
        Check if an event matches a pattern.
        
        Pattern format (EventBridge-like):
        {
            "source": ["minio"],
            "detail-type": ["ObjectCreated"],
            "detail": {
                "bucket": ["raw", "uploads"]
            }
        }
        """
        for key, expected_values in pattern.items():
            if key == "detail":
                # Nested matching for detail object
                event_detail = event.get("detail", {})
                if not self._match_detail(event_detail, expected_values):
                    return False
            else:
                event_value = event.get(key)
                if not self._match_value(event_value, expected_values):
                    return False
        
        return True
    
    def _match_value(self, actual: Any, expected: Any) -> bool:
        """Match a single value against expected values."""
        if isinstance(expected, list):
            return actual in expected
        return actual == expected
    
    def _match_detail(self, detail: Dict, pattern: Dict) -> bool:
        """Match detail object fields."""
        for key, expected in pattern.items():
            actual = detail.get(key)
            if not self._match_value(actual, expected):
                return False
        return True


class TargetDispatcher:
    """Dispatches events to target services (Temporal, Functions, etc.)."""
    
    async def dispatch(self, target: Dict[str, Any], event: Dict[str, Any]) -> bool:
        """
        Dispatch an event to a target.
        
        Target format:
        {
            "type": "workflow",  # or "function", "queue"
            "name": "doc_ingest_workflow",
            "input_path": "$.detail"  # Optional: extract input from event
        }
        """
        target_type = target.get("type")
        target_name = target.get("name")
        
        logger.info(f"Dispatching to {target_type}:{target_name}")
        
        if target_type == "workflow":
            return await self._start_workflow(target_name, event)
        elif target_type == "function":
            return await self._invoke_function(target_name, event)
        elif target_type == "queue":
            return await self._send_to_queue(target_name, event)
        else:
            logger.warning(f"Unknown target type: {target_type}")
            return False
    
    async def _start_workflow(self, workflow_name: str, event: Dict) -> bool:
        """Start a Temporal workflow."""
        try:
            # In production, use temporalio client
            # from temporalio.client import Client
            # client = await Client.connect(TEMPORAL_HOST)
            # await client.start_workflow(workflow_name, event, id=..., task_queue=...)
            
            logger.info(f"[TEMPORAL] Starting workflow: {workflow_name}")
            logger.info(f"[TEMPORAL] Input: {json.dumps(event, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            return False
    
    async def _invoke_function(self, function_name: str, event: Dict) -> bool:
        """Invoke a function (container)."""
        try:
            # In production, this would call your function runtime
            logger.info(f"[FUNCTION] Invoking: {function_name}")
            logger.info(f"[FUNCTION] Payload: {json.dumps(event, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"Failed to invoke function: {e}")
            return False
    
    async def _send_to_queue(self, queue_name: str, event: Dict) -> bool:
        """Send event to another queue/topic."""
        try:
            logger.info(f"[QUEUE] Sending to: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send to queue: {e}")
            return False


class EventRouter:
    """
    Main Event Router service.
    Subscribes to NATS subjects, matches events against rules, and dispatches to targets.
    """
    
    def __init__(self):
        self.nc: Optional[NATS] = None
        self.matcher = EventMatcher()
        self.dispatcher = TargetDispatcher()
        self.rules: List[EventRule] = []
    
    async def connect(self):
        """Connect to NATS server."""
        logger.info(f"Connecting to NATS at {NATS_URL}")
        self.nc = await nats.connect(NATS_URL)
        logger.info("Connected to NATS successfully")
    
    async def load_rules(self):
        """Load event rules from database."""
        # In production, load from PostgreSQL
        # For now, use sample rules
        self.rules = [
            EventRule(
                id="rule-1",
                name="minio-to-workflow",
                project_id="default",
                event_pattern={
                    "source": ["minio"],
                    "detail-type": ["ObjectCreated"],
                    "detail": {
                        "bucket": ["raw", "uploads"]
                    }
                },
                targets=[
                    {"type": "workflow", "name": "doc_ingest_workflow"}
                ]
            ),
            EventRule(
                id="rule-2",
                name="notify-on-workflow-complete",
                project_id="default",
                event_pattern={
                    "source": ["temporal"],
                    "detail-type": ["WorkflowCompleted"]
                },
                targets=[
                    {"type": "function", "name": "send_notification"}
                ]
            )
        ]
        logger.info(f"Loaded {len(self.rules)} event rules")
    
    async def handle_event(self, msg):
        """Handle incoming NATS message."""
        try:
            subject = msg.subject
            data = msg.data.decode()
            
            logger.info(f"Received event on {subject}")
            
            event = json.loads(data)
            
            # Add source from subject if not present
            if "source" not in event:
                event["source"] = subject.split(".")[0]
            
            # Match against all rules
            matched_rules = [
                rule for rule in self.rules
                if rule.enabled and self.matcher.matches(event, rule.event_pattern)
            ]
            
            logger.info(f"Matched {len(matched_rules)} rules")
            
            # Dispatch to all targets
            for rule in matched_rules:
                for target in rule.targets:
                    await self.dispatcher.dispatch(target, event)
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    async def start(self):
        """Start the event router."""
        await self.connect()
        await self.load_rules()
        
        # Subscribe to all event sources
        subjects = [
            "minio.>",      # MinIO events: minio.bucket.object.created
            "temporal.>",   # Temporal events
            "function.>",   # Function events
            "api.>",        # API events
            "events.>",     # Generic events
        ]
        
        for subject in subjects:
            await self.nc.subscribe(subject, cb=self.handle_event)
            logger.info(f"Subscribed to: {subject}")
        
        logger.info("Event Router started. Waiting for events...")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the event router."""
        if self.nc:
            await self.nc.drain()
            logger.info("Disconnected from NATS")


async def main():
    """Entry point."""
    router = EventRouter()
    
    try:
        await router.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await router.stop()


if __name__ == "__main__":
    asyncio.run(main())
