# 🚀 MiniCloud Platform

## Self-Hosted AWS-like Control Plane

A complete cloud platform that replicates AWS core services using open-source tools. Run your own cloud infrastructure with Organizations, IAM, Object Storage, Workflows, Events, and Observability.

---

## 🎯 What is this?

MiniCloud Platform is a **self-hosted cloud control plane** that provides:

- **AWS Organizations** → Multi-tenant hierarchy (Orgs → Projects)
- **AWS IAM** → Policy-based access control with evaluation engine
- **AWS S3** → Object storage via MinIO
- **AWS Lambda** → Serverless functions (container-based)
- **AWS Step Functions** → Durable workflows via Temporal
- **AWS EventBridge** → Event routing via NATS
- **AWS CloudWatch** → Observability via Prometheus + Grafana + Loki
- **AWS CloudTrail** → Audit logging in PostgreSQL

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   FastAPI   │  │   Policy    │  │     Resource Registry   │  │
│  │     API     │  │   Engine    │  │      (PostgreSQL)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         DATA PLANE                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐  │
│  │  MinIO  │  │ Temporal│  │  NATS   │  │ Airflow │  │Workers│  │
│  │(Storage)│  │(Workflow│  │ (Events)│  │ (Batch) │  │(Funcs)│  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └───────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       OBSERVABILITY                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Prometheus  │  │   Grafana   │  │          Loki           │  │
│  │  (Metrics)  │  │ (Dashboards)│  │         (Logs)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
minicloud-platform/
├── api/                    # FastAPI Control Plane API
│   └── main.py             # All REST endpoints
├── core/                   # Core business logic
│   ├── policy_engine.py    # IAM policy evaluation
│   └── event_router.py     # Event routing (EventBridge-like)
├── workers/                # Temporal workers
│   └── main.py             # Workflow & Activity definitions
├── database/               # Database schemas
│   └── schema.sql          # PostgreSQL schema (14 tables)
├── ui/                     # React Dashboard (MiniCloud Console)
│   ├── src/App.jsx         # Main application component
│   ├── src/index.css       # Design system (AWS-inspired dark theme)
│   └── package.json        # Frontend dependencies
├── observability/          # Monitoring configuration
│   └── prometheus.yml      # Prometheus scrape config
├── docker-compose.yml      # Full platform orchestration (13 services)
├── Dockerfile.api          # API service container
├── Dockerfile.worker       # Worker service container
├── Dockerfile.router       # Event router container
├── Dockerfile.ui           # React UI container (nginx)
└── requirements.txt        # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended

### Start the Platform

```bash
# Clone and start
git clone <repo-url>
cd minicloud-platform
docker-compose up --build
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MiniCloud Console** | http://localhost:3000 | - |
| **API (Swagger)** | http://localhost:8000/docs | - |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **Temporal UI** | http://localhost:8080 | - |
| **Airflow** | http://localhost:8081 | admin / admin |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **NATS Monitor** | http://localhost:8222 | - |

---

## 🔐 IAM Policy System

MiniCloud uses AWS IAM-style policies:

```json
{
  "Version": "2024-01-01",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["minio:GetObject", "minio:PutObject"],
      "Resource": ["bucket:raw/*", "bucket:processed/*"],
      "Condition": {
        "IpAddress": {"aws:SourceIp": "10.0.0.0/8"}
      }
    }
  ]
}
```

### Policy Evaluation Logic

1. ❌ **Explicit DENY** always wins
2. ✅ **Explicit ALLOW** grants access
3. ❌ **Implicit DENY** (default)

---

## 📡 Event Routing

Events flow through NATS and are routed to targets based on rules:

```json
{
  "name": "process-uploads",
  "event_pattern": {
    "source": ["minio"],
    "detail-type": ["ObjectCreated"],
    "detail": {"bucket": ["raw"]}
  },
  "targets": [
    {"type": "workflow", "name": "doc_ingest_workflow"}
  ]
}
```

### Event Flow

```
MinIO Upload → NATS Event → Event Router → Temporal Workflow → Result
```

---

## ⚙️ Workflows (Step Functions)

Workflows are durable, resumable, and support:

- **Retries** with exponential backoff
- **Timeouts** per activity
- **Human approval** via signals
- **Compensation** (saga pattern)

### Example Workflow

```python
class DocumentIngestWorkflow:
    async def run(self, input):
        # 1. Fetch from MinIO
        doc = await fetch_from_minio(input["bucket"], input["key"])
        
        # 2. Process with function
        result = await invoke_function("process_doc", doc)
        
        # 3. Store result
        await store_to_minio("processed", f"result_{input['key']}", result)
        
        # 4. Notify
        await send_notification("slack", "Document processed!")
        
        return {"status": "COMPLETED"}
```

---

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `orgs` | Organizations (tenants) |
| `projects` | Projects within orgs (AWS Accounts) |
| `users` | IAM users |
| `roles` | IAM roles |
| `policies` | IAM policy documents |
| `role_bindings` | User-role assignments |
| `role_policies` | Role-policy attachments |
| `resources` | All platform resources |
| `resource_versions` | Resource version history |
| `event_rules` | Event routing rules |
| `audit_log` | Complete audit trail |
| `metering_usage` | Usage tracking |
| `api_keys` | Programmatic access keys |
| `workflow_runs` | Workflow execution history |

---

## 🛠️ API Endpoints

### Organizations & Projects
- `POST /api/v1/orgs` - Create organization
- `POST /api/v1/orgs/{id}/projects` - Create project

### IAM
- `POST /api/v1/orgs/{id}/users` - Create user
- `POST /api/v1/orgs/{id}/policies` - Create policy
- `POST /api/v1/policies/simulate` - Test policy evaluation

### Resources
- `POST /api/v1/projects/{id}/resources` - Create resource
- `GET /api/v1/projects/{id}/resources` - List resources

### Storage
- `POST /api/v1/projects/{id}/buckets` - Create bucket
- `GET /api/v1/projects/{id}/buckets` - List buckets

### Functions
- `POST /api/v1/projects/{id}/functions` - Deploy function
- `POST /api/v1/functions/{id}/invoke` - Invoke function

### Workflows
- `POST /api/v1/projects/{id}/workflows` - Register workflow
- `POST /api/v1/workflows/{name}/start` - Start execution

### Events
- `POST /api/v1/projects/{id}/event-rules` - Create routing rule

### Audit & Metering
- `GET /api/v1/orgs/{id}/audit-logs` - Query audit logs
- `GET /api/v1/projects/{id}/usage` - Get usage metrics

---

## 🎓 What This Project Demonstrates

This repository showcases:

- ✅ **Distributed systems design** (Control Plane vs Data Plane)
- ✅ **IAM policy engine** with AWS-compatible syntax
- ✅ **Event-driven architecture** with message routing
- ✅ **Durable workflows** with Temporal
- ✅ **Multi-tenancy** with organizations and projects
- ✅ **Full observability** (metrics, logs, traces)
- ✅ **Audit & compliance** with append-only logs
- ✅ **GitOps-ready** resource management

---

## 📝 Resume Bullet Points

**Short:**
> Built a self-hosted AWS-like cloud platform with IAM, object storage, event routing, and durable workflows using FastAPI, PostgreSQL, MinIO, NATS, and Temporal.

**Detailed:**
> Designed and implemented a multi-tenant cloud control plane featuring AWS IAM-compatible policy evaluation, EventBridge-style event routing, Step Functions-like durable workflows, and complete observability stack. Demonstrated distributed systems architecture separating control plane and data plane concerns.

---

## 🔮 Future Enhancements

- [x] React UI Dashboard ✅
- [ ] Kubernetes operator for resource provisioning
- [ ] OpenTelemetry distributed tracing
- [ ] Rate limiting and quotas
- [ ] SSO with Keycloak integration
- [ ] Terraform provider

---

## 📄 License

MIT License
