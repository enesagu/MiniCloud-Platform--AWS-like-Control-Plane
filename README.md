# 🚀 MiniCloud Platform

## Self-Hosted AWS-like Control Plane

A complete cloud platform that replicates AWS core services using open-source tools. Run your own cloud infrastructure with Organizations, IAM, Object Storage, Serverless Functions, Compute Instances, Workflows, Events, and Observability — all with a beautiful React Dashboard.

![MiniCloud Console](https://img.shields.io/badge/UI-React%20Dashboard-61DAFB?style=flat&logo=react)
![API](https://img.shields.io/badge/API-FastAPI-009688?style=flat&logo=fastapi)
![Storage](https://img.shields.io/badge/Storage-MinIO-C72E49?style=flat&logo=minio)
![Workflows](https://img.shields.io/badge/Workflows-Temporal-000000?style=flat)
![Events](https://img.shields.io/badge/Events-NATS-27AAE1?style=flat)

---

## ✨ Features

### Core Platform
- 🏢 **Multi-tenant Organizations** — Org → Project hierarchy
- 🔐 **IAM Policy Engine** — AWS-compatible policy evaluation
- 📦 **Object Storage** — S3-compatible via MinIO with real CRUD
- 🖥️ **Compute Instances** — EC2-like VM/container lifecycle management
- ⚡ **Serverless Functions** — Real Lambda-like execution with code editor
- 🔄 **Durable Workflows** — Temporal-powered workflow orchestration
- 📡 **Event Routing** — EventBridge-style pattern matching
- 📬 **Messaging** — SNS Topics + SQS Queues
- 📊 **Full Observability** — Prometheus + Grafana + Loki

### MiniCloud Console (React UI)
- 🎨 **AWS Console-inspired dark theme**
- 📱 **Responsive design** with modern UI components
- 🔗 **Real API integration** — All operations persist to database
- 📈 **Live stats and usage metrics**
- 📝 **Audit log viewer** with search and CSV export
- 🔧 **Policy simulator** for testing IAM rules
- 💻 **Code editor** for serverless functions

---

## 🆕 Recent Updates

### ✅ Compute Instances (EC2-like)
- **Instance Lifecycle Management** — Launch, Stop, Start, Reboot, Terminate
- **Compute Hosts** — View cluster nodes with CPU/Memory allocation
- **State Machine** — 15 states from REQUESTED → RUNNING → TERMINATED
- **Temporal Workflows** — Durable provisioning with retry/rollback
- **Event Audit Trail** — Complete state transition history

### ✅ Real Function Runtime
- **Actual Code Execution** — Handler return values captured and returned
- **stdout Capture** — print() statements appear in logs
- **Exception Handling** — Errors return status: FAILED with traceback
- **Duration Tracking** — Real execution time measured
- **Lambda Context** — AWS-compatible context object

### ✅ Code Editor for Functions
- **Syntax-highlighted editor** with dark theme
- **Runtime templates** — Python, Node.js, Go, Java
- **Test panel** — Invoke with JSON payload
- **Configuration view** — Runtime, memory, timeout

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UI LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              MiniCloud Console (React + Vite)                │    │
│  │  Dashboard | Instances | Functions | Buckets | Workflows     │    │
│  │  Topics | Queues | Event Rules | IAM | Audit Logs            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                               │ HTTP/REST
┌─────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │   FastAPI   │  │   Policy    │  │     Resource Registry       │  │
│  │     API     │  │   Engine    │  │      (PostgreSQL)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PLANE                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐  │
│  │  MinIO  │  │ Temporal│  │  NATS   │  │ Airflow │  │  Event    │  │
│  │(Storage)│  │(Workflow)│  │ (Events)│  │ (Batch) │  │  Router   │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                       OBSERVABILITY                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ Prometheus  │  │   Grafana   │  │          Loki               │  │
│  │  (Metrics)  │  │ (Dashboards)│  │         (Logs)              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Instance Lifecycle (Temporal Orchestration)

```
User Request → API → InstanceService → Temporal Workflow
                                            ↓
              ┌─────────────────────────────────────────────┐
              │       ProvisionInstanceWorkflow             │
              │       (Durable State Machine)               │
              ├─────────────────────────────────────────────┤
              │ 1. ValidateRequest (quota, IAM, image)      │
              │ 2. SelectHost (placement policy)            │
              │ 3. ProvisionOnHost (agent command)          │
              │ 4. [Wait for Agent Signal]                  │
              │ 5. ConfigureNetwork (IP, DNS, firewall)     │
              │ 6. HealthCheck (ping, port check)           │
              │ 7. → RUNNING ✅                             │
              │                                             │
              │ On Failure → ROLLING_BACK → FAILED          │
              └─────────────────────────────────────────────┘
```

### Instance States
| State | Description |
|-------|-------------|
| `REQUESTED` | Initial request received |
| `VALIDATING` | Checking quota, permissions, image |
| `SCHEDULING` | Selecting compute host |
| `PROVISIONING` | Creating VM/container on host |
| `BOOTSTRAPPING` | Running cloud-init/startup script |
| `CONFIGURING_NETWORK` | Attaching network, assigning IP |
| `HEALTHCHECKING` | Verifying instance health |
| `RUNNING` | Instance is up and healthy |
| `STOPPING` | Graceful shutdown in progress |
| `STOPPED` | Instance paused (can restart) |
| `TERMINATING` | Destroying instance |
| `TERMINATED` | Instance destroyed |
| `FAILED` | Provisioning failed |
| `ROLLING_BACK` | Cleaning up after failure |

---

## ⚡ Function Runtime

MiniCloud now includes a **real Lambda-like runtime** that executes your code:

```python
def handler(event, context):
    """Your function code - this actually runs!"""
    number = event.get('number', 5)
    
    # Calculate factorial
    result = 1
    for i in range(1, number + 1):
        result *= i
    
    # This return value is captured and returned to the caller
    return {
        "statusCode": 200,
        "body": {
            "number": number,
            "factorial": result
        }
    }
```

### Invoke Response
```json
{
  "function_id": "abc123",
  "function_name": "factorial",
  "status": "SUCCESS",
  "response": {
    "statusCode": 200,
    "body": {
      "number": 5,
      "factorial": 120
    }
  },
  "duration_ms": 15,
  "logs": [
    "START RequestId: abc123",
    "Function: factorial",
    "Runtime: python3.10",
    "Handler returned: dict",
    "END RequestId: abc123",
    "Duration: 15ms"
  ]
}
```

---

## 🗂️ Project Structure

```
minicloud-platform/
├── api/                        # FastAPI Control Plane API
│   ├── main.py                 # Application setup
│   ├── routers.py              # REST endpoints
│   ├── services.py             # Business logic (incl. real function runtime)
│   ├── repositories.py         # Data access layer
│   └── models.py               # Pydantic schemas
├── core/                       # Core business logic
│   ├── policy_engine.py        # IAM policy evaluation engine
│   └── event_router.py         # NATS event routing service
├── workers/                    # Temporal workers
│   ├── main.py                 # General workflow definitions
│   └── instance_workflows.py   # Instance lifecycle orchestration
├── database/                   # Database schemas
│   ├── schema.sql              # PostgreSQL schema (18 tables)
│   └── 00_create_databases.sql # Init script
├── ui/                         # React Dashboard
│   ├── src/
│   │   ├── api.js              # API service client
│   │   ├── App.jsx             # Main app with routing
│   │   ├── index.css           # Design system
│   │   ├── hooks/              # Custom hooks
│   │   ├── components/         # Reusable UI
│   │   └── pages/              # Page components
│   │       ├── Dashboard.jsx   # Overview stats
│   │       ├── Instances.jsx   # EC2-like compute ⭐ NEW
│   │       ├── Functions.jsx   # Lambda with code editor ⭐ NEW
│   │       ├── Buckets.jsx     # S3 storage
│   │       ├── Workflows.jsx   # Step Functions
│   │       ├── Topics.jsx      # SNS
│   │       ├── Queues.jsx      # SQS
│   │       ├── EventRules.jsx  # EventBridge
│   │       ├── IAM.jsx         # Users & policies
│   │       └── AuditLogs.jsx   # Activity logs
│   └── nginx.conf              # Production config
├── observability/              # Monitoring
│   └── prometheus.yml          # Scrape config
├── docker-compose.yml          # Full orchestration (15 services)
└── Makefile                    # Helper commands
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended

### Start the Platform

```bash
# Clone the repository
git clone <repo-url>
cd minicloud-platform

# Start all services (first run takes a few minutes)
docker-compose up --build

# Or use make
make up
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **🎨 MiniCloud Console** | http://localhost:3000 | - |
| **📚 API Docs (Swagger)** | http://localhost:8000/docs | - |
| **📦 MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **🔄 Temporal UI** | http://localhost:8080 | - |
| **📊 Grafana** | http://localhost:3001 | admin / admin |
| **📈 Prometheus** | http://localhost:9090 | - |
| **📡 NATS Monitor** | http://localhost:8222 | - |

---

## 🖥️ MiniCloud Console

### Pages & Features

| Page | Features |
|------|----------|
| **Dashboard** | Resource stats, usage metrics, recent activity |
| **Instances** | Launch/Stop/Start/Terminate instances, compute hosts view ⭐ |
| **Functions** | Code editor, runtime selection, test panel, invoke ⭐ |
| **Buckets** | Create/delete buckets (real MinIO), browse objects |
| **Workflows** | Register workflows, start executions, view history |
| **Topics** | SNS-like pub/sub, subscriptions, publish messages |
| **Queues** | SQS-like message queues, send/receive messages |
| **Event Rules** | EventBridge-style rules with pattern matching |
| **IAM** | Users, policies, **Policy Simulator** |
| **Audit Logs** | Search/filter logs, export to CSV |

---

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `organizations` | Tenants (top-level) |
| `projects` | Projects within orgs |
| `users` | IAM users |
| `roles` | IAM roles |
| `policies` | IAM policy documents |
| `role_bindings` | User-role assignments |
| `role_policies` | Role-policy attachments |
| `resources` | Functions, workflows, etc. |
| `hosts` | Compute nodes ⭐ NEW |
| `instances` | VM/containers ⭐ NEW |
| `instance_events` | State transition audit ⭐ NEW |
| `event_rules` | Event routing rules |
| `topics` | SNS topics |
| `subscriptions` | Topic subscriptions |
| `queues` | SQS queues |
| `audit_logs` | Complete audit trail |
| `workflow_runs` | Workflow execution history |
| `metering_usage` | Usage tracking |

---

## 🛠️ API Endpoints

### Instances (EC2-like) ⭐ NEW
- `POST /api/v1/projects/{id}/instances` — Launch instance
- `GET /api/v1/projects/{id}/instances` — List instances
- `GET /api/v1/instances/{id}` — Get instance details
- `POST /api/v1/instances/{id}/stop` — Stop instance
- `POST /api/v1/instances/{id}/start` — Start instance
- `POST /api/v1/instances/{id}/reboot` — Reboot instance
- `POST /api/v1/instances/{id}/terminate` — Terminate instance
- `GET /api/v1/instances/{id}/events` — State transition audit

### Hosts ⭐ NEW
- `GET /api/v1/hosts` — List compute hosts
- `GET /api/v1/hosts/{id}` — Get host details
- `GET /api/v1/hosts/{id}/instances` — List instances on host

### Functions (Lambda-like)
- `POST /api/v1/projects/{id}/functions` — Deploy function with code
- `GET /api/v1/projects/{id}/functions` — List functions
- `GET /api/v1/projects/{id}/functions/{fid}` — Get function details
- `PUT /api/v1/functions/{id}/code` — Update function code
- `POST /api/v1/functions/{id}/invoke` — **Execute function (real runtime)**
- `DELETE /api/v1/projects/{id}/functions/{fid}` — Delete function

### Storage (S3-like)
- `POST /api/v1/projects/{id}/buckets?name=...` — Create bucket
- `GET /api/v1/projects/{id}/buckets` — List buckets with stats
- `DELETE /api/v1/projects/{id}/buckets/{name}` — Delete bucket

### Messaging
- `POST /api/v1/projects/{id}/topics` — Create topic
- `POST /api/v1/projects/{id}/topics/{tid}/publish` — Publish message
- `POST /api/v1/projects/{id}/queues` — Create queue
- `POST /api/v1/projects/{id}/queues/{qid}/messages` — Send message

### Workflows (Step Functions)
- `POST /api/v1/projects/{id}/workflows` — Register workflow
- `POST /api/v1/workflows/{name}/start` — Start execution
- `GET /api/v1/workflows/{name}/runs` — List executions

### Events (EventBridge)
- `POST /api/v1/projects/{id}/event-rules` — Create routing rule
- `DELETE /api/v1/projects/{id}/event-rules/{rid}` — Delete rule

### IAM
- `POST /api/v1/orgs/{id}/users` — Create user
- `POST /api/v1/orgs/{id}/policies` — Create policy
- `POST /api/v1/policies/simulate` — Test policy evaluation

### Audit
- `GET /api/v1/orgs/{id}/audit-logs` — Query audit logs
- `GET /api/v1/projects/{id}/usage` — Usage metrics

---

## 🎓 What This Project Demonstrates

- ✅ **Distributed systems design** — Control Plane vs Data Plane
- ✅ **Full-stack development** — FastAPI + React
- ✅ **Real function runtime** — Lambda-like code execution
- ✅ **Instance lifecycle** — EC2-like state machine with Temporal
- ✅ **Database design** — Multi-tenant schema with 18 tables
- ✅ **IAM policy engine** — AWS-compatible syntax
- ✅ **Event-driven architecture** — NATS + pattern routing
- ✅ **Durable workflows** — Temporal integration
- ✅ **Container orchestration** — Docker Compose with 15 services
- ✅ **CI/CD** — GitHub Actions pipeline
- ✅ **Observability** — Metrics, logs, health checks
- ✅ **Modern UI** — React with professional design system

---

## 📝 Resume Bullet Points

**Short:**
> Built a self-hosted AWS-like cloud platform with React dashboard, IAM policy engine, real Lambda runtime, EC2-like compute instances with Temporal orchestration, S3-compatible storage, and full observability stack.

**Detailed:**
> Designed and implemented a multi-tenant cloud control plane featuring a React console, real serverless function execution, EC2-like instance lifecycle management with Temporal durable workflows, AWS IAM-compatible policy engine, S3-compatible object storage, SNS/SQS messaging, EventBridge-style routing, and comprehensive CI/CD pipeline with Prometheus/Grafana observability.

---

## 🔮 Roadmap

- [x] React UI Dashboard ✅
- [x] Real database integration ✅
- [x] MinIO bucket CRUD ✅
- [x] GitHub Actions CI/CD ✅
- [x] Policy Simulator ✅
- [x] Audit log export ✅
- [x] SNS Topics & SQS Queues ✅
- [x] **Real function execution (Lambda runtime)** ✅ NEW
- [x] **Compute instances (EC2-like)** ✅ NEW
- [x] **Temporal instance lifecycle workflows** ✅ NEW
- [x] **Code editor for functions** ✅ NEW
- [ ] Kubernetes operator for resource provisioning
- [ ] OpenTelemetry distributed tracing
- [ ] Rate limiting and quotas
- [ ] SSO with Keycloak integration
- [ ] Terraform provider
- [ ] Node.js function runtime

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📄 License

MIT License
