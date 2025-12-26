"""
MiniCloud Platform - Instance Lifecycle Workflows
Full AWS Step Functions + EventBridge equivalent for VM/Container orchestration.

This is the "brain" of the platform - handles:
- Instance provisioning with retries
- State machine transitions
- Agent callbacks via signals
- Rollback on failure
- Audit trail
"""

import asyncio
import os
import uuid
import json
import logging
from datetime import timedelta, datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

# Temporal imports (uncomment in production)
# from temporalio import activity, workflow
# from temporalio.client import Client
# from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("instance-workflows")

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "minicloud-instance-tasks"


# =====================================================
# INSTANCE STATES (State Machine)
# =====================================================

class InstanceState(str, Enum):
    """Instance lifecycle states - AWS EC2-like state machine"""
    REQUESTED = "REQUESTED"           # Initial request received
    VALIDATING = "VALIDATING"         # Validating request & permissions
    SCHEDULING = "SCHEDULING"         # Selecting host/placement
    PROVISIONING = "PROVISIONING"     # Creating VM/container on host
    BOOTSTRAPPING = "BOOTSTRAPPING"   # Running cloud-init/startup scripts
    CONFIGURING_NETWORK = "CONFIGURING_NETWORK"  # Network attachment
    HEALTHCHECKING = "HEALTHCHECKING" # Waiting for health checks
    RUNNING = "RUNNING"               # Instance is up and healthy
    STOPPING = "STOPPING"             # Graceful shutdown in progress
    STOPPED = "STOPPED"               # Instance stopped (can restart)
    TERMINATING = "TERMINATING"       # Destroying instance
    TERMINATED = "TERMINATED"         # Instance destroyed
    FAILED = "FAILED"                 # Provisioning failed
    ROLLING_BACK = "ROLLING_BACK"     # Cleaning up after failure


@dataclass
class InstanceSpec:
    """Instance specification - what the user requested"""
    name: str
    project_id: str
    cpu: int = 2
    memory_mb: int = 2048
    disk_gb: int = 20
    image: str = "ubuntu:22.04"
    network_segment: str = "default"
    startup_script: str = ""
    tags: Dict[str, str] = None
    sla_timeout_seconds: int = 120  # How long before we fail
    
    def __post_init__(self):
        self.tags = self.tags or {}


@dataclass 
class InstanceStatus:
    """Current instance status"""
    instance_id: str
    state: InstanceState
    host_id: Optional[str] = None
    ip_address: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = None
    updated_at: str = None


# =====================================================
# ACTIVITIES (Individual units of work)
# =====================================================

# @activity.defn
async def validate_instance_request(spec: Dict) -> Dict[str, Any]:
    """
    Activity: Validate the instance request
    - Check quota
    - Check IAM permissions
    - Validate image
    - Check resource availability
    """
    logger.info(f"[Activity] Validating instance request: {spec.get('name')}")
    
    # Simulate validation checks
    errors = []
    
    # Check required fields
    if not spec.get("name"):
        errors.append("Instance name is required")
    
    # Check memory limits
    memory = spec.get("memory_mb", 0)
    if memory < 512:
        errors.append("Minimum memory is 512MB")
    if memory > 32768:
        errors.append("Maximum memory is 32GB")
    
    # Check CPU limits
    cpu = spec.get("cpu", 0)
    if cpu < 1:
        errors.append("Minimum 1 CPU required")
    if cpu > 16:
        errors.append("Maximum 16 CPUs allowed")
    
    # Check quota (simulated)
    current_instances = 5  # Would query DB
    quota_limit = 50
    if current_instances >= quota_limit:
        errors.append(f"Instance quota exceeded ({quota_limit})")
    
    # Check image allowed list
    allowed_images = ["ubuntu:22.04", "ubuntu:20.04", "debian:11", "alpine:3.18", "centos:8"]
    if spec.get("image") not in allowed_images:
        errors.append(f"Image not allowed. Use: {allowed_images}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "spec": spec,
        "validated_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def select_host(spec: Dict) -> Dict[str, Any]:
    """
    Activity: Select the best host for the instance
    - Query available hosts
    - Check resource availability
    - Apply placement policies
    - Score and select
    """
    logger.info(f"[Activity] Selecting host for instance: {spec.get('name')}")
    
    # Simulated host inventory
    available_hosts = [
        {"id": "host-001", "name": "compute-node-1", "cpu_free": 8, "memory_free_mb": 16384, "zone": "zone-a", "score": 0},
        {"id": "host-002", "name": "compute-node-2", "cpu_free": 4, "memory_free_mb": 8192, "zone": "zone-a", "score": 0},
        {"id": "host-003", "name": "compute-node-3", "cpu_free": 12, "memory_free_mb": 24576, "zone": "zone-b", "score": 0},
    ]
    
    required_cpu = spec.get("cpu", 2)
    required_memory = spec.get("memory_mb", 2048)
    preferred_zone = spec.get("zone", None)
    
    # Filter hosts with enough resources
    viable_hosts = [
        h for h in available_hosts
        if h["cpu_free"] >= required_cpu and h["memory_free_mb"] >= required_memory
    ]
    
    if not viable_hosts:
        return {
            "selected": False,
            "error": "No hosts with sufficient resources available",
            "host_id": None
        }
    
    # Score hosts (higher is better)
    for host in viable_hosts:
        score = 0
        # Prefer hosts with more free resources (bin packing inverse)
        score += (host["cpu_free"] - required_cpu) * 10
        score += (host["memory_free_mb"] - required_memory) // 100
        # Prefer same zone if specified
        if preferred_zone and host["zone"] == preferred_zone:
            score += 50
        host["score"] = score
    
    # Select best host
    best_host = max(viable_hosts, key=lambda h: h["score"])
    
    logger.info(f"[Activity] Selected host: {best_host['name']} (score: {best_host['score']})")
    
    return {
        "selected": True,
        "host_id": best_host["id"],
        "host_name": best_host["name"],
        "zone": best_host["zone"],
        "scheduled_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def provision_on_host(host_id: str, instance_id: str, spec: Dict) -> Dict[str, Any]:
    """
    Activity: Send provision command to host agent
    In production, this would call the agent API on the host.
    The agent then creates the VM/container.
    """
    logger.info(f"[Activity] Provisioning instance {instance_id} on host {host_id}")
    
    # Simulate sending command to agent
    provision_command = {
        "action": "CREATE_INSTANCE",
        "instance_id": instance_id,
        "spec": {
            "cpu": spec.get("cpu", 2),
            "memory_mb": spec.get("memory_mb", 2048),
            "disk_gb": spec.get("disk_gb", 20),
            "image": spec.get("image", "ubuntu:22.04"),
            "startup_script": spec.get("startup_script", ""),
        }
    }
    
    # In production: await agent_client.send_command(host_id, provision_command)
    logger.info(f"[Activity] Sent provision command to agent: {json.dumps(provision_command)}")
    
    # Simulate async provision start
    await asyncio.sleep(1)
    
    return {
        "provision_started": True,
        "host_id": host_id,
        "instance_id": instance_id,
        "command_id": str(uuid.uuid4()),
        "started_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def configure_network(instance_id: str, host_id: str, network_segment: str) -> Dict[str, Any]:
    """
    Activity: Configure networking for the instance
    - Attach to network segment
    - Assign IP
    - Configure firewall rules
    - Register in service discovery
    """
    logger.info(f"[Activity] Configuring network for instance {instance_id}")
    
    # Simulate network configuration
    assigned_ip = f"10.0.{hash(instance_id) % 256}.{hash(instance_id) % 256}"
    
    # In production:
    # - Call network controller to attach instance to segment
    # - Get assigned IP
    # - Apply security groups
    # - Register DNS
    
    return {
        "success": True,
        "instance_id": instance_id,
        "network_segment": network_segment,
        "ip_address": assigned_ip,
        "dns_name": f"{instance_id}.minicloud.local",
        "configured_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def health_check_instance(instance_id: str, ip_address: str, timeout_seconds: int = 60) -> Dict[str, Any]:
    """
    Activity: Check if instance is healthy
    - Ping IP
    - Check agent heartbeat
    - Verify SSH/API availability
    """
    logger.info(f"[Activity] Health checking instance {instance_id} at {ip_address}")
    
    # Simulate health check with retries
    max_attempts = timeout_seconds // 5
    
    for attempt in range(max_attempts):
        # In production: actual health check
        # - await asyncio.wait_for(check_ssh(ip_address), timeout=5)
        # - await agent_client.heartbeat(instance_id)
        
        # Simulate random success after a few attempts
        if attempt >= 2:
            return {
                "healthy": True,
                "instance_id": instance_id,
                "ip_address": ip_address,
                "attempts": attempt + 1,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        await asyncio.sleep(5)
    
    return {
        "healthy": False,
        "instance_id": instance_id,
        "error": "Health check timeout",
        "attempts": max_attempts
    }


# @activity.defn
async def rollback_instance(instance_id: str, host_id: str, reason: str) -> Dict[str, Any]:
    """
    Activity: Rollback/cleanup failed instance
    - Remove from host
    - Release network resources
    - Update status
    """
    logger.info(f"[Activity] Rolling back instance {instance_id}: {reason}")
    
    cleanup_steps = []
    
    # Step 1: Stop instance on host
    # await agent_client.stop_instance(host_id, instance_id)
    cleanup_steps.append("Instance stopped on host")
    
    # Step 2: Release network
    # await network_controller.release_ip(instance_id)
    cleanup_steps.append("Network resources released")
    
    # Step 3: Release disk
    # await storage_controller.release_disk(instance_id)
    cleanup_steps.append("Storage released")
    
    return {
        "success": True,
        "instance_id": instance_id,
        "reason": reason,
        "cleanup_steps": cleanup_steps,
        "rolled_back_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def update_instance_state(instance_id: str, state: str, details: Dict = None) -> Dict[str, Any]:
    """
    Activity: Update instance state in database
    Also logs to audit trail.
    """
    logger.info(f"[Activity] Updating instance {instance_id} state to {state}")
    
    # In production: update PostgreSQL
    # await db.execute(
    #     "UPDATE instances SET state = $1, details = $2, updated_at = NOW() WHERE id = $3",
    #     state, json.dumps(details or {}), instance_id
    # )
    
    # Audit log
    # await db.execute(
    #     "INSERT INTO audit_logs (action, resource_type, resource_id, details) VALUES ($1, $2, $3, $4)",
    #     f"InstanceState:{state}", "instance", instance_id, json.dumps(details or {})
    # )
    
    return {
        "instance_id": instance_id,
        "state": state,
        "details": details,
        "updated_at": datetime.utcnow().isoformat()
    }


# @activity.defn
async def send_notification(channel: str, message: str, instance_id: str) -> bool:
    """Activity: Send notification about instance event"""
    logger.info(f"[Activity] Notification [{channel}]: {message}")
    return True


# =====================================================
# WORKFLOWS (Orchestration Logic)
# =====================================================

# @workflow.defn
class ProvisionInstanceWorkflow:
    """
    Main Instance Lifecycle Orchestrator
    
    This workflow manages the entire lifecycle of an instance:
    REQUESTED → VALIDATING → SCHEDULING → PROVISIONING → 
    BOOTSTRAPPING → CONFIGURING_NETWORK → HEALTHCHECKING → RUNNING
    
    On failure: → ROLLING_BACK → FAILED
    
    Temporal ensures:
    - Durable state (survives crashes)
    - Retries with backoff
    - Timeouts and SLA enforcement
    - Signals for external callbacks (agent provisioned)
    - Queries for current state
    """
    
    def __init__(self):
        self.state = InstanceState.REQUESTED
        self.instance_id = None
        self.host_id = None
        self.ip_address = None
        self.error = None
        self.provisioned_signal_received = False
    
    # @workflow.signal
    def signal_provisioned(self, ip_address: str, boot_logs: str = ""):
        """
        Signal: Agent reports instance is provisioned
        Called externally when host agent completes VM/container creation.
        """
        logger.info(f"[Signal] Instance provisioned with IP: {ip_address}")
        self.ip_address = ip_address
        self.provisioned_signal_received = True
    
    # @workflow.signal
    def signal_stop(self):
        """Signal: Request instance stop"""
        logger.info(f"[Signal] Stop requested for instance {self.instance_id}")
        self.state = InstanceState.STOPPING
    
    # @workflow.signal  
    def signal_terminate(self):
        """Signal: Request instance termination"""
        logger.info(f"[Signal] Terminate requested for instance {self.instance_id}")
        self.state = InstanceState.TERMINATING
    
    # @workflow.query
    def get_state(self) -> Dict[str, Any]:
        """Query: Get current instance state"""
        return {
            "instance_id": self.instance_id,
            "state": self.state.value,
            "host_id": self.host_id,
            "ip_address": self.ip_address,
            "error": self.error
        }
    
    # @workflow.run
    async def run(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Main workflow execution"""
        self.instance_id = spec.get("instance_id", str(uuid.uuid4()))
        sla_timeout = spec.get("sla_timeout_seconds", 120)
        
        logger.info(f"[Workflow] Starting ProvisionInstanceWorkflow for {self.instance_id}")
        
        try:
            # ========== STEP 1: VALIDATE ==========
            self.state = InstanceState.VALIDATING
            await update_instance_state(self.instance_id, self.state.value)
            
            validation = await validate_instance_request(spec)
            if not validation["valid"]:
                self.error = f"Validation failed: {validation['errors']}"
                raise Exception(self.error)
            
            # ========== STEP 2: SCHEDULE ==========
            self.state = InstanceState.SCHEDULING
            await update_instance_state(self.instance_id, self.state.value)
            
            scheduling = await select_host(spec)
            if not scheduling["selected"]:
                self.error = scheduling["error"]
                raise Exception(self.error)
            
            self.host_id = scheduling["host_id"]
            
            # ========== STEP 3: PROVISION ==========
            self.state = InstanceState.PROVISIONING
            await update_instance_state(self.instance_id, self.state.value, {
                "host_id": self.host_id
            })
            
            provision_result = await provision_on_host(
                self.host_id, self.instance_id, spec
            )
            
            # Wait for agent signal (with timeout)
            # In production: await workflow.wait_condition(lambda: self.provisioned_signal_received, timeout=timedelta(seconds=sla_timeout))
            logger.info(f"[Workflow] Waiting for provision signal (timeout: {sla_timeout}s)...")
            
            # Simulate waiting for signal
            await asyncio.sleep(2)
            self.signal_provisioned(f"10.0.{hash(self.instance_id) % 256}.{hash(self.instance_id) % 256}")
            
            if not self.provisioned_signal_received:
                self.error = "Provision timeout - agent did not respond"
                raise Exception(self.error)
            
            # ========== STEP 4: BOOTSTRAP ==========
            self.state = InstanceState.BOOTSTRAPPING
            await update_instance_state(self.instance_id, self.state.value, {
                "ip_address": self.ip_address
            })
            
            # Bootstrap happens on the instance itself (cloud-init)
            # We just wait/monitor
            await asyncio.sleep(1)
            
            # ========== STEP 5: CONFIGURE NETWORK ==========
            self.state = InstanceState.CONFIGURING_NETWORK
            await update_instance_state(self.instance_id, self.state.value)
            
            network_config = await configure_network(
                self.instance_id, 
                self.host_id,
                spec.get("network_segment", "default")
            )
            
            # ========== STEP 6: HEALTH CHECK ==========
            self.state = InstanceState.HEALTHCHECKING
            await update_instance_state(self.instance_id, self.state.value)
            
            health = await health_check_instance(
                self.instance_id,
                self.ip_address,
                timeout_seconds=60
            )
            
            if not health["healthy"]:
                self.error = "Health check failed"
                raise Exception(self.error)
            
            # ========== STEP 7: RUNNING ==========
            self.state = InstanceState.RUNNING
            await update_instance_state(self.instance_id, self.state.value, {
                "ip_address": self.ip_address,
                "host_id": self.host_id,
                "dns_name": network_config.get("dns_name")
            })
            
            await send_notification(
                "slack",
                f"Instance {spec.get('name')} is now RUNNING at {self.ip_address}",
                self.instance_id
            )
            
            logger.info(f"[Workflow] Instance {self.instance_id} is RUNNING!")
            
            return {
                "status": "SUCCESS",
                "instance_id": self.instance_id,
                "state": self.state.value,
                "host_id": self.host_id,
                "ip_address": self.ip_address,
                "dns_name": network_config.get("dns_name")
            }
            
        except Exception as e:
            # ========== ROLLBACK ==========
            logger.error(f"[Workflow] Instance provisioning failed: {e}")
            
            self.state = InstanceState.ROLLING_BACK
            await update_instance_state(self.instance_id, self.state.value, {
                "error": str(e)
            })
            
            if self.host_id:
                await rollback_instance(self.instance_id, self.host_id, str(e))
            
            self.state = InstanceState.FAILED
            await update_instance_state(self.instance_id, self.state.value, {
                "error": str(e)
            })
            
            await send_notification(
                "slack",
                f"Instance {spec.get('name')} FAILED: {e}",
                self.instance_id
            )
            
            return {
                "status": "FAILED",
                "instance_id": self.instance_id,
                "state": self.state.value,
                "error": str(e)
            }


# @workflow.defn
class TerminateInstanceWorkflow:
    """Workflow to gracefully terminate an instance"""
    
    # @workflow.run
    async def run(self, instance_id: str, force: bool = False) -> Dict[str, Any]:
        logger.info(f"[Workflow] Terminating instance {instance_id}")
        
        # Get instance details from DB
        # instance = await db.fetchrow("SELECT * FROM instances WHERE id = $1", instance_id)
        
        # Update state
        await update_instance_state(instance_id, InstanceState.TERMINATING.value)
        
        # Graceful shutdown (if not force)
        if not force:
            # Send shutdown signal to instance
            await asyncio.sleep(30)  # Wait for graceful shutdown
        
        # Cleanup
        await rollback_instance(instance_id, "host-unknown", "User requested termination")
        
        # Update final state
        await update_instance_state(instance_id, InstanceState.TERMINATED.value)
        
        return {
            "status": "TERMINATED",
            "instance_id": instance_id
        }


# @workflow.defn
class StopInstanceWorkflow:
    """Workflow to stop (pause) an instance"""
    
    # @workflow.run
    async def run(self, instance_id: str) -> Dict[str, Any]:
        logger.info(f"[Workflow] Stopping instance {instance_id}")
        
        await update_instance_state(instance_id, InstanceState.STOPPING.value)
        
        # Send stop command to host agent
        # await agent_client.stop_instance(host_id, instance_id)
        await asyncio.sleep(5)
        
        await update_instance_state(instance_id, InstanceState.STOPPED.value)
        
        return {
            "status": "STOPPED",
            "instance_id": instance_id
        }


# @workflow.defn
class StartInstanceWorkflow:
    """Workflow to start a stopped instance"""
    
    # @workflow.run
    async def run(self, instance_id: str) -> Dict[str, Any]:
        logger.info(f"[Workflow] Starting instance {instance_id}")
        
        # Send start command to host agent
        # await agent_client.start_instance(host_id, instance_id)
        
        await update_instance_state(instance_id, InstanceState.BOOTSTRAPPING.value)
        await asyncio.sleep(2)
        
        # Health check
        await update_instance_state(instance_id, InstanceState.HEALTHCHECKING.value)
        await asyncio.sleep(3)
        
        await update_instance_state(instance_id, InstanceState.RUNNING.value)
        
        return {
            "status": "RUNNING",
            "instance_id": instance_id
        }


# =====================================================
# WORKER SETUP
# =====================================================

async def run_instance_worker():
    """Start the Temporal worker for instance workflows"""
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
    
    # In production:
    # client = await Client.connect(TEMPORAL_HOST)
    # worker = Worker(
    #     client,
    #     task_queue=TASK_QUEUE,
    #     workflows=[
    #         ProvisionInstanceWorkflow,
    #         TerminateInstanceWorkflow,
    #         StopInstanceWorkflow,
    #         StartInstanceWorkflow
    #     ],
    #     activities=[
    #         validate_instance_request,
    #         select_host,
    #         provision_on_host,
    #         configure_network,
    #         health_check_instance,
    #         rollback_instance,
    #         update_instance_state,
    #         send_notification
    #     ]
    # )
    # await worker.run()
    
    logger.info("Instance Worker started")
    logger.info("Workflows: ProvisionInstance, TerminateInstance, StopInstance, StartInstance")
    logger.info("Activities: 8 registered")
    
    # Keep alive
    while True:
        await asyncio.sleep(60)
        logger.info("Instance Worker heartbeat...")


async def main():
    """Demo: Run a provision workflow locally"""
    logger.info("=== Demo: Instance Provision Workflow ===")
    
    spec = {
        "name": "my-web-server",
        "project_id": "proj-default",
        "cpu": 2,
        "memory_mb": 4096,
        "disk_gb": 40,
        "image": "ubuntu:22.04",
        "network_segment": "web-tier",
        "startup_script": "apt-get update && apt-get install -y nginx",
        "tags": {"env": "production", "app": "web"},
        "sla_timeout_seconds": 120
    }
    
    workflow = ProvisionInstanceWorkflow()
    result = await workflow.run(spec)
    
    logger.info(f"=== Result ===")
    logger.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
