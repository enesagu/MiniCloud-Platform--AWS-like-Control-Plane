"""
MiniCloud Platform - Temporal Worker
Executes workflow activities (Step Functions equivalent).
"""

import asyncio
import os
import logging
from datetime import timedelta
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Note: In production, uncomment and use actual temporalio imports
# from temporalio import activity, workflow
# from temporalio.client import Client
# from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("temporal-worker")

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "minicloud-tasks"


# =====================================================
# ACTIVITIES (Individual units of work)
# =====================================================

# @activity.defn
async def validate_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate incoming data."""
    logger.info(f"[Activity] Validating input: {input_data}")
    
    required_fields = input_data.get("required_fields", [])
    data = input_data.get("data", {})
    
    missing = [f for f in required_fields if f not in data]
    
    return {
        "valid": len(missing) == 0,
        "missing_fields": missing,
        "data": data
    }


# @activity.defn
async def fetch_from_minio(bucket: str, key: str) -> Dict[str, Any]:
    """Fetch an object from MinIO."""
    logger.info(f"[Activity] Fetching from MinIO: {bucket}/{key}")
    
    # In production, use minio client
    # from minio import Minio
    # client = Minio(...)
    # response = client.get_object(bucket, key)
    
    return {
        "bucket": bucket,
        "key": key,
        "size_bytes": 1024,
        "content_type": "application/json",
        "data": {"sample": "data"}
    }


# @activity.defn
async def store_to_minio(bucket: str, key: str, data: Any) -> Dict[str, Any]:
    """Store an object to MinIO."""
    logger.info(f"[Activity] Storing to MinIO: {bucket}/{key}")
    
    return {
        "bucket": bucket,
        "key": key,
        "success": True,
        "etag": "abc123"
    }


# @activity.defn
async def invoke_function(function_name: str, payload: Dict) -> Dict[str, Any]:
    """Invoke a function and return result."""
    logger.info(f"[Activity] Invoking function: {function_name}")
    
    # In production, call your function runtime
    return {
        "function": function_name,
        "status": "SUCCESS",
        "response": {"processed": True},
        "duration_ms": 150
    }


# @activity.defn
async def send_notification(channel: str, message: str) -> bool:
    """Send a notification (email, slack, webhook)."""
    logger.info(f"[Activity] Sending notification to {channel}: {message}")
    return True


# @activity.defn
async def write_to_database(table: str, data: Dict) -> Dict[str, Any]:
    """Write data to PostgreSQL."""
    logger.info(f"[Activity] Writing to database table: {table}")
    
    return {
        "table": table,
        "rows_affected": 1,
        "id": "generated-uuid"
    }


# @activity.defn
async def wait_for_approval(request_id: str, timeout_hours: int = 24) -> Dict[str, Any]:
    """
    Wait for human approval (uses Temporal signals).
    This is a placeholder - actual implementation uses workflow signals.
    """
    logger.info(f"[Activity] Waiting for approval: {request_id}")
    
    return {
        "request_id": request_id,
        "approved": True,
        "approver": "admin@example.com"
    }


# =====================================================
# WORKFLOWS (Orchestration logic)
# =====================================================

# @workflow.defn
class DocumentIngestWorkflow:
    """
    Example workflow: Process a document uploaded to MinIO.
    
    Steps:
    1. Fetch document from MinIO
    2. Validate format
    3. Process with function
    4. Store result
    5. Notify completion
    """
    
    # @workflow.run
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[Workflow] Document Ingest started: {input}")
        
        bucket = input.get("bucket", "raw")
        key = input.get("key", "document.pdf")
        
        # Step 1: Fetch from MinIO
        doc = await fetch_from_minio(bucket, key)
        
        # Step 2: Validate
        validation = await validate_input({
            "required_fields": ["content_type"],
            "data": doc
        })
        
        if not validation["valid"]:
            return {"status": "FAILED", "reason": "Validation failed"}
        
        # Step 3: Process with function
        result = await invoke_function("process_document", {"doc": doc})
        
        # Step 4: Store result
        await store_to_minio("processed", f"result_{key}", result)
        
        # Step 5: Notify
        await send_notification("slack", f"Document {key} processed successfully")
        
        return {
            "status": "COMPLETED",
            "input_key": key,
            "output_key": f"result_{key}"
        }


# @workflow.defn  
class ApprovalWorkflow:
    """
    Example workflow: Request with human approval step.
    
    Steps:
    1. Submit request
    2. Wait for human approval (signal)
    3. Execute approved action
    4. Notify result
    """
    
    # @workflow.run
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[Workflow] Approval Workflow started: {input}")
        
        request_type = input.get("type", "general")
        request_data = input.get("data", {})
        
        # Step 1: Record request
        record = await write_to_database("approval_requests", {
            "type": request_type,
            "data": request_data,
            "status": "PENDING"
        })
        
        # Step 2: Notify approvers
        await send_notification(
            "email",
            f"New {request_type} request pending approval"
        )
        
        # Step 3: Wait for approval (in real Temporal, this uses signals)
        approval = await wait_for_approval(record["id"])
        
        if not approval["approved"]:
            return {"status": "REJECTED", "request_id": record["id"]}
        
        # Step 4: Execute action
        await invoke_function(f"execute_{request_type}", request_data)
        
        # Step 5: Notify completion
        await send_notification(
            "email",
            f"Request {record['id']} has been approved and executed"
        )
        
        return {
            "status": "APPROVED",
            "request_id": record["id"],
            "approver": approval["approver"]
        }


# @workflow.defn
class DataPipelineWorkflow:
    """
    Example workflow: ETL-style data pipeline.
    
    Steps:
    1. Extract data from source
    2. Transform with function
    3. Load to destination
    4. Record lineage
    """
    
    # @workflow.run
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[Workflow] Data Pipeline started: {input}")
        
        source_bucket = input.get("source_bucket", "raw")
        source_key = input.get("source_key")
        dest_bucket = input.get("dest_bucket", "processed")
        transform_fn = input.get("transform_function", "default_transform")
        
        # Extract
        data = await fetch_from_minio(source_bucket, source_key)
        
        # Transform
        transformed = await invoke_function(transform_fn, data)
        
        # Load
        dest_key = f"transformed_{source_key}"
        await store_to_minio(dest_bucket, dest_key, transformed)
        
        # Record lineage
        await write_to_database("data_lineage", {
            "source": f"{source_bucket}/{source_key}",
            "destination": f"{dest_bucket}/{dest_key}",
            "transform": transform_fn
        })
        
        return {
            "status": "COMPLETED",
            "source": f"{source_bucket}/{source_key}",
            "destination": f"{dest_bucket}/{dest_key}"
        }


# =====================================================
# WORKER STARTUP
# =====================================================

async def run_worker():
    """Start the Temporal worker."""
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
    
    # In production:
    # client = await Client.connect(TEMPORAL_HOST)
    # worker = Worker(
    #     client,
    #     task_queue=TASK_QUEUE,
    #     workflows=[DocumentIngestWorkflow, ApprovalWorkflow, DataPipelineWorkflow],
    #     activities=[
    #         validate_input,
    #         fetch_from_minio,
    #         store_to_minio,
    #         invoke_function,
    #         send_notification,
    #         write_to_database,
    #         wait_for_approval
    #     ]
    # )
    # await worker.run()
    
    logger.info(f"Worker started on task queue: {TASK_QUEUE}")
    logger.info("Registered workflows: DocumentIngestWorkflow, ApprovalWorkflow, DataPipelineWorkflow")
    logger.info("Registered activities: 7 activities")
    
    # Keep alive for demo
    while True:
        await asyncio.sleep(60)
        logger.info("Worker heartbeat...")


async def main():
    """Entry point."""
    try:
        await run_worker()
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
