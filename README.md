# 🚀 MiniCloud Platform

## Self-Hosted AWS-like Control Plane

A complete cloud platform that replicates AWS core services using open-source tools. Run your own cloud infrastructure with Organizations, IAM, Object Storage, Workflows, Events, and Observability — all with a beautiful React Dashboard.

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
- ⚡ **Serverless Functions** — Create, invoke, and manage functions
- 🔄 **Durable Workflows** — Temporal-powered workflow orchestration
- 📡 **Event Routing** — EventBridge-style pattern matching
- 📊 **Full Observability** — Prometheus + Grafana + Loki

### MiniCloud Console (React UI)
- 🎨 **AWS Console-inspired dark theme**
- 📱 **Responsive design** with modern UI components
- 🔗 **Real API integration** — All operations persist to database
- 📈 **Live stats and usage metrics**
- 📝 **Audit log viewer** with search and CSV export
- 🔧 **Policy simulator** for testing IAM rules

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UI LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              MiniCloud Console (React + Vite)                │    │
│  │   Dashboard | Functions | Buckets | Workflows | IAM | Logs   │    │
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

## 🗂️ Project Structure

```
minicloud-platform/
├── api/                        # FastAPI Control Plane API
│   └── main.py                 # REST endpoints with DB/MinIO integration
├── core/                       # Core business logic
│   ├── policy_engine.py        # IAM policy evaluation engine
│   └── event_router.py         # NATS event routing service
├── workers/                    # Temporal workers
│   └── main.py                 # Workflow & Activity definitions
├── database/                   # Database schemas
│   ├── schema.sql              # PostgreSQL schema (13 tables)
│   └── 00_create_databases.sql # Init script for Airflow/Temporal DBs
├── ui/                         # React Dashboard (MiniCloud Console)
│   ├── src/
│   │   ├── api.js              # API service client
│   │   ├── App.jsx             # Main application with routing
│   │   ├── index.css           # Professional design system
│   │   ├── hooks/              # Custom React hooks
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ui.jsx          # Button, Card, Modal, Table, etc.
│   │   │   └── Layout.jsx      # Sidebar, Header, PageLayout
│   │   └── pages/              # Page components
│   │       ├── Dashboard.jsx   # Overview with stats
│   │       ├── Functions.jsx   # Function CRUD + invoke
│   │       ├── Buckets.jsx     # Bucket management (MinIO)
│   │       ├── Workflows.jsx   # Workflow management
│   │       ├── EventRules.jsx  # Event routing rules
│   │       ├── IAM.jsx         # Users, Policies, Simulator
│   │       └── AuditLogs.jsx   # Log viewer with export
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.js          # Vite configuration
│   └── nginx.conf              # Production nginx config
├── observability/              # Monitoring configuration
│   └── prometheus.yml          # Prometheus scrape config
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD pipeline
├── docker-compose.yml          # Full platform orchestration (13 services)
├── Dockerfile.api              # API service container
├── Dockerfile.worker           # Temporal worker container
├── Dockerfile.router           # Event router container
├── Dockerfile.ui               # React UI container (nginx)
├── Makefile                    # Helper commands
└── requirements.txt            # Python dependencies
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

# Start all services (first run will take a few minutes)
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

The React-based dashboard provides a complete management interface:

### Pages & Features

| Page | Features |
|------|----------|
| **Dashboard** | Resource stats, usage metrics, recent activity, quick overview |
| **Functions** | Create functions with runtime/memory config, invoke with JSON payload, view results |
| **Buckets** | Create/delete buckets (real MinIO), browse objects, view storage stats |
| **Workflows** | Register workflows, start executions, view run history, link to Temporal UI |
| **Event Rules** | Create EventBridge-style rules with pattern matching and targets |
| **IAM** | Manage users, create policies, **Policy Simulator** for testing access |
| **Audit Logs** | Search/filter logs, export to CSV, real-time activity feed |

### UI Components

- Professional dark theme (AWS Console-inspired)
- Reusable components: Button, Card, Modal, Table, Status badges
- Form components: Input, Select, Textarea with validation
- Loading states, empty states, error handling
- Responsive design

---

## 🔐 IAM Policy System

MiniCloud uses AWS IAM-style policies with a full evaluation engine:

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

### Policy Simulator

Test access decisions without making real requests:

```bash
POST /api/v1/policies/simulate?action=minio:GetObject&resource=bucket:raw/file.pdf
```

---

## 📡 Event Routing

Events flow through NATS and are routed to targets based on pattern rules:

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

Workflows are powered by Temporal for durability and reliability:

- **Automatic retries** with exponential backoff
- **Timeouts** per activity
- **Human approval** via signals
- **Compensation** (saga pattern)
- **Versioning** for safe deployments

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
| `resources` | All platform resources (functions, workflows, etc.) |
| `event_rules` | Event routing rules |
| `audit_logs` | Complete audit trail |
| `workflow_runs` | Workflow execution history |
| `metering_usage` | Usage tracking |
| `api_keys` | Programmatic access keys |

---

## 🛠️ API Endpoints

### Organizations & Projects
- `POST /api/v1/orgs` — Create organization
- `POST /api/v1/orgs/{id}/projects` — Create project

### IAM
- `POST /api/v1/orgs/{id}/users` — Create user
- `DELETE /api/v1/orgs/{id}/users/{uid}` — Delete user
- `POST /api/v1/orgs/{id}/policies` — Create policy
- `POST /api/v1/policies/simulate` — Test policy evaluation

### Storage (MinIO)
- `POST /api/v1/projects/{id}/buckets?name=...` — Create bucket
- `GET /api/v1/projects/{id}/buckets` — List buckets with stats
- `DELETE /api/v1/projects/{id}/buckets/{name}` — Delete bucket

### Functions
- `POST /api/v1/projects/{id}/functions` — Deploy function
- `GET /api/v1/projects/{id}/functions` — List functions
- `POST /api/v1/functions/{id}/invoke` — Invoke function
- `DELETE /api/v1/projects/{id}/functions/{fid}` — Delete function

### Workflows
- `POST /api/v1/projects/{id}/workflows` — Register workflow
- `POST /api/v1/workflows/{name}/start` — Start execution
- `GET /api/v1/workflows/{name}/runs` — List executions

### Events
- `POST /api/v1/projects/{id}/event-rules` — Create routing rule
- `DELETE /api/v1/projects/{id}/event-rules/{rid}` — Delete rule

### Audit & Usage
- `GET /api/v1/orgs/{id}/audit-logs` — Query audit logs
- `GET /api/v1/projects/{id}/usage` — Get usage metrics

---

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) includes:

- **Backend**: Python linting (flake8), type checking (mypy), tests (pytest)
- **Frontend**: Node.js build, lint
- **Docker**: Multi-service builds with caching
- **Integration**: Tests with PostgreSQL and NATS
- **Security**: Trivy vulnerability scanning

---

## 🎓 What This Project Demonstrates

This repository showcases:

- ✅ **Distributed systems design** — Control Plane vs Data Plane separation
- ✅ **Full-stack development** — FastAPI backend + React frontend
- ✅ **Database design** — Multi-tenant schema with proper relationships
- ✅ **IAM policy engine** — AWS-compatible syntax and evaluation
- ✅ **Event-driven architecture** — NATS messaging with pattern routing
- ✅ **Durable workflows** — Temporal integration
- ✅ **Container orchestration** — Docker Compose with 13 services
- ✅ **CI/CD** — GitHub Actions pipeline
- ✅ **Observability** — Metrics, logs, and health checks
- ✅ **Modern UI** — React with professional design system

---

## 📝 Resume Bullet Points

**Short:**
> Built a self-hosted AWS-like cloud platform with React dashboard, IAM policy engine, object storage (MinIO), event routing (NATS), and durable workflows (Temporal) using FastAPI and PostgreSQL.

**Detailed:**
> Designed and implemented a multi-tenant cloud control plane featuring a React-based management console, AWS IAM-compatible policy evaluation engine, S3-compatible object storage with MinIO, EventBridge-style event routing, and Step Functions-like durable workflows. Includes full CI/CD pipeline and observability stack with Prometheus, Grafana, and Loki.

---

## 🔮 Roadmap

- [x] React UI Dashboard ✅
- [x] Real database integration ✅
- [x] MinIO bucket CRUD ✅
- [x] GitHub Actions CI/CD ✅
- [x] Policy Simulator ✅
- [x] Audit log export ✅
- [ ] Kubernetes operator for resource provisioning
- [ ] OpenTelemetry distributed tracing
- [ ] Rate limiting and quotas
- [ ] SSO with Keycloak integration
- [ ] Terraform provider
- [ ] Real function execution (container runtime)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📄 License

MIT License
