import React, { useState, useEffect } from 'react'
import { 
  Cloud, Database, Folder, Code, GitBranch, Bell, Zap, 
  Shield, Users, Settings, BarChart3, Activity, Box,
  Plus, Search, ChevronRight, ArrowUpRight, ArrowDownRight,
  Play, Pause, CheckCircle2, AlertCircle, Clock, Terminal,
  HardDrive, Network, FileCode, Workflow, Key, FileText
} from 'lucide-react'

// ========================================
// API Service
// ========================================
const API_BASE = '/api/v1'

const api = {
  async get(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`)
    return res.json()
  },
  async post(endpoint, data) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return res.json()
  }
}

// ========================================
// Layout Components
// ========================================
function Sidebar({ activePage, setActivePage }) {
  const navItems = [
    { section: 'Overview', items: [
      { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    ]},
    { section: 'Compute', items: [
      { id: 'functions', label: 'Functions', icon: Code, badge: '3' },
      { id: 'workflows', label: 'Workflows', icon: GitBranch },
    ]},
    { section: 'Storage', items: [
      { id: 'buckets', label: 'Buckets', icon: Folder },
    ]},
    { section: 'Integration', items: [
      { id: 'events', label: 'Event Rules', icon: Zap },
      { id: 'topics', label: 'Topics', icon: Network },
    ]},
    { section: 'Security', items: [
      { id: 'iam', label: 'IAM', icon: Shield },
      { id: 'policies', label: 'Policies', icon: FileText },
      { id: 'api-keys', label: 'API Keys', icon: Key },
    ]},
    { section: 'Observability', items: [
      { id: 'logs', label: 'Logs', icon: Terminal },
      { id: 'metrics', label: 'Metrics', icon: Activity },
    ]},
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Cloud size={20} />
        </div>
        <div>
          <div className="sidebar-title">MiniCloud</div>
          <div className="sidebar-subtitle">Control Plane</div>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map(section => (
          <div key={section.section} className="nav-section">
            <div className="nav-section-title">{section.section}</div>
            {section.items.map(item => (
              <div 
                key={item.id}
                className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => setActivePage(item.id)}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
                {item.badge && <span className="nav-item-badge">{item.badge}</span>}
              </div>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  )
}

function Header({ title, breadcrumb }) {
  return (
    <header className="header">
      <div className="header-left">
        <div className="breadcrumb">
          <span>MiniCloud</span>
          <ChevronRight size={14} className="breadcrumb-separator" />
          <span className="breadcrumb-current">{title}</span>
        </div>
      </div>
      
      <div className="header-right">
        <input 
          type="text" 
          className="header-search" 
          placeholder="Search resources... (⌘K)"
        />
        
        <div className="header-user">
          <div className="header-user-avatar">A</div>
          <div className="header-user-info">
            <div className="header-user-name">Admin</div>
            <div className="header-user-role">Organization Owner</div>
          </div>
        </div>
      </div>
    </header>
  )
}

// ========================================
// Dashboard Page
// ========================================
function DashboardPage() {
  const stats = [
    { label: 'Active Functions', value: '12', change: '+2', positive: true, icon: Code, color: 'purple' },
    { label: 'Storage Buckets', value: '8', change: '+1', positive: true, icon: Folder, color: 'blue' },
    { label: 'Running Workflows', value: '3', change: '0', positive: true, icon: GitBranch, color: 'green' },
    { label: 'Event Rules', value: '15', change: '+5', positive: true, icon: Zap, color: 'yellow' },
  ]

  const recentActivity = [
    { type: 'success', icon: CheckCircle2, text: 'Workflow doc_ingest completed successfully', time: '2 min ago' },
    { type: 'info', icon: Play, text: 'Function resize_image deployed', time: '15 min ago' },
    { type: 'warning', icon: AlertCircle, text: 'Bucket uploads approaching quota', time: '1 hour ago' },
    { type: 'info', icon: Zap, text: 'Event rule minio-to-workflow triggered', time: '2 hours ago' },
  ]

  const resources = [
    { type: 'bucket', name: 'raw-uploads', status: 'Active', size: '2.4 GB' },
    { type: 'bucket', name: 'processed', status: 'Active', size: '1.8 GB' },
    { type: 'function', name: 'process-document', status: 'Active', invocations: '1,234' },
    { type: 'function', name: 'send-notification', status: 'Active', invocations: '892' },
    { type: 'workflow', name: 'doc-ingest-pipeline', status: 'Running', runs: '45' },
  ]

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">Overview of your MiniCloud resources and activity</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {stats.map((stat, i) => (
          <div key={i} className="stat-card slide-up" style={{ animationDelay: `${i * 50}ms` }}>
            <div className={`stat-icon ${stat.color}`}>
              <stat.icon size={20} />
            </div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className={`stat-change ${stat.positive ? 'positive' : 'negative'}`}>
              {stat.positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {stat.change} this week
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Activity size={16} />
              Recent Activity
            </div>
            <button className="btn btn-sm btn-secondary">View All</button>
          </div>
          <div className="card-body">
            <div className="activity-list">
              {recentActivity.map((item, i) => (
                <div key={i} className="activity-item">
                  <div className={`activity-icon stat-icon ${
                    item.type === 'success' ? 'green' : 
                    item.type === 'warning' ? 'yellow' : 'blue'
                  }`}>
                    <item.icon size={16} />
                  </div>
                  <div className="activity-content">
                    <div className="activity-text">{item.text}</div>
                    <div className="activity-time">{item.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Resources */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Box size={16} />
              Resources
            </div>
            <button className="btn btn-sm btn-primary">
              <Plus size={14} />
              Create
            </button>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {resources.map((res, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div className={`resource-icon ${res.type}`}>
                            {res.type === 'bucket' ? <Folder size={14} /> :
                             res.type === 'function' ? <Code size={14} /> :
                             <GitBranch size={14} />}
                          </div>
                          <span className="code">{res.name}</span>
                        </div>
                      </td>
                      <td style={{ textTransform: 'capitalize' }}>{res.type}</td>
                      <td>
                        <span className={`status status-${res.status.toLowerCase()}`}>
                          <span className="status-dot"></span>
                          {res.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Functions Page
// ========================================
function FunctionsPage() {
  const [showModal, setShowModal] = useState(false)
  
  const functions = [
    { name: 'process-document', runtime: 'python3.10', memory: 256, timeout: 30, status: 'Active', invocations: 1234 },
    { name: 'resize-image', runtime: 'nodejs18.x', memory: 512, timeout: 60, status: 'Active', invocations: 892 },
    { name: 'send-notification', runtime: 'python3.10', memory: 128, timeout: 10, status: 'Active', invocations: 3421 },
  ]

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Functions</h1>
          <p className="page-description">Deploy and manage serverless functions</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} />
          Create Function
        </button>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Runtime</th>
                <th>Memory</th>
                <th>Timeout</th>
                <th>Status</th>
                <th>Invocations</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {functions.map((fn, i) => (
                <tr key={i}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div className="resource-icon function">
                        <Code size={14} />
                      </div>
                      <span className="code">{fn.name}</span>
                    </div>
                  </td>
                  <td><span className="code">{fn.runtime}</span></td>
                  <td>{fn.memory} MB</td>
                  <td>{fn.timeout}s</td>
                  <td>
                    <span className="status status-active">
                      <span className="status-dot"></span>
                      {fn.status}
                    </span>
                  </td>
                  <td>{fn.invocations.toLocaleString()}</td>
                  <td>
                    <button className="btn btn-sm btn-secondary">
                      <Play size={12} />
                      Invoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <CreateFunctionModal onClose={() => setShowModal(false)} />
      )}
    </div>
  )
}

function CreateFunctionModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Create Function</div>
          <button className="btn btn-sm btn-secondary" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">Function Name</label>
            <input type="text" className="form-input" placeholder="my-function" />
          </div>
          <div className="form-group">
            <label className="form-label">Runtime</label>
            <select className="form-input">
              <option>python3.10</option>
              <option>python3.9</option>
              <option>nodejs18.x</option>
              <option>nodejs16.x</option>
              <option>go1.x</option>
            </select>
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Memory (MB)</label>
              <input type="number" className="form-input" defaultValue={128} />
            </div>
            <div className="form-group">
              <label className="form-label">Timeout (seconds)</label>
              <input type="number" className="form-input" defaultValue={30} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Handler</label>
            <input type="text" className="form-input" placeholder="main.handler" />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary">Create Function</button>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Buckets Page
// ========================================
function BucketsPage() {
  const buckets = [
    { name: 'raw-uploads', objects: 1234, size: '2.4 GB', created: '2024-01-15', status: 'Active' },
    { name: 'processed', objects: 892, size: '1.8 GB', created: '2024-01-15', status: 'Active' },
    { name: 'backups', objects: 45, size: '12.5 GB', created: '2024-02-01', status: 'Active' },
    { name: 'temp', objects: 23, size: '156 MB', created: '2024-03-10', status: 'Active' },
  ]

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Storage Buckets</h1>
          <p className="page-description">S3-compatible object storage powered by MinIO</p>
        </div>
        <button className="btn btn-primary">
          <Plus size={16} />
          Create Bucket
        </button>
      </div>

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-icon blue"><HardDrive size={20} /></div>
          <div className="stat-value">16.9 GB</div>
          <div className="stat-label">Total Storage Used</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Folder size={20} /></div>
          <div className="stat-value">4</div>
          <div className="stat-label">Active Buckets</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><FileCode size={20} /></div>
          <div className="stat-value">2,194</div>
          <div className="stat-label">Total Objects</div>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Objects</th>
                <th>Size</th>
                <th>Created</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {buckets.map((bucket, i) => (
                <tr key={i}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div className="resource-icon bucket">
                        <Folder size={14} />
                      </div>
                      <span className="code">{bucket.name}</span>
                    </div>
                  </td>
                  <td>{bucket.objects.toLocaleString()}</td>
                  <td>{bucket.size}</td>
                  <td>{bucket.created}</td>
                  <td>
                    <span className="status status-active">
                      <span className="status-dot"></span>
                      {bucket.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-secondary">Browse</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Workflows Page
// ========================================
function WorkflowsPage() {
  const workflows = [
    { name: 'doc-ingest-pipeline', status: 'Running', runs: 45, lastRun: '2 min ago', avgDuration: '12s' },
    { name: 'approval-workflow', status: 'Active', runs: 23, lastRun: '1 hour ago', avgDuration: '4h' },
    { name: 'data-pipeline', status: 'Active', runs: 156, lastRun: '5 min ago', avgDuration: '45s' },
  ]

  const recentRuns = [
    { workflow: 'doc-ingest-pipeline', runId: 'run-abc123', status: 'Completed', duration: '11s', time: '2 min ago' },
    { workflow: 'data-pipeline', runId: 'run-def456', status: 'Running', duration: '23s', time: '5 min ago' },
    { workflow: 'doc-ingest-pipeline', runId: 'run-ghi789', status: 'Completed', duration: '14s', time: '15 min ago' },
    { workflow: 'approval-workflow', runId: 'run-jkl012', status: 'Waiting', duration: '3h 20m', time: '1 hour ago' },
  ]

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Workflows</h1>
          <p className="page-description">Durable workflow orchestration powered by Temporal</p>
        </div>
        <button className="btn btn-primary">
          <Plus size={16} />
          Register Workflow
        </button>
      </div>

      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* Workflow Definitions */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Workflow size={16} />
              Workflow Definitions
            </div>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Runs</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {workflows.map((wf, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div className="resource-icon workflow">
                            <GitBranch size={14} />
                          </div>
                          <div>
                            <div className="code">{wf.name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                              Last run: {wf.lastRun}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>{wf.runs}</td>
                      <td>
                        <span className={`status status-${wf.status.toLowerCase()}`}>
                          <span className="status-dot"></span>
                          {wf.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Clock size={16} />
              Recent Executions
            </div>
            <button className="btn btn-sm btn-secondary">View All</button>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Duration</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRuns.map((run, i) => (
                    <tr key={i}>
                      <td>
                        <div>
                          <div className="code">{run.runId}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                            {run.workflow}
                          </div>
                        </div>
                      </td>
                      <td>{run.duration}</td>
                      <td>
                        <span className={`status status-${
                          run.status === 'Completed' ? 'active' :
                          run.status === 'Running' ? 'running' :
                          'pending'
                        }`}>
                          <span className="status-dot"></span>
                          {run.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ========================================
// IAM Page
// ========================================
function IAMPage() {
  const users = [
    { name: 'admin', email: 'admin@example.com', role: 'Admin', lastLogin: '10 min ago', status: 'Active' },
    { name: 'developer', email: 'dev@example.com', role: 'Developer', lastLogin: '2 hours ago', status: 'Active' },
    { name: 'viewer', email: 'viewer@example.com', role: 'Viewer', lastLogin: '1 day ago', status: 'Active' },
  ]

  const roles = [
    { name: 'Admin', description: 'Full access to all resources', users: 1, policies: 1 },
    { name: 'Developer', description: 'Create and manage resources', users: 1, policies: 2 },
    { name: 'Viewer', description: 'Read-only access', users: 1, policies: 1 },
  ]

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Identity & Access Management</h1>
        <p className="page-description">Manage users, roles, and permissions</p>
      </div>

      <div className="grid-2">
        {/* Users */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Users size={16} />
              Users
            </div>
            <button className="btn btn-sm btn-primary">
              <Plus size={14} />
              Add User
            </button>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div className="header-user-avatar" style={{ width: 28, height: 28, fontSize: 11 }}>
                            {user.name[0].toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontWeight: 500 }}>{user.name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td><span className="code">{user.role}</span></td>
                      <td>
                        <span className="status status-active">
                          <span className="status-dot"></span>
                          {user.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Roles */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Shield size={16} />
              Roles
            </div>
            <button className="btn btn-sm btn-primary">
              <Plus size={14} />
              Create Role
            </button>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Users</th>
                    <th>Policies</th>
                  </tr>
                </thead>
                <tbody>
                  {roles.map((role, i) => (
                    <tr key={i}>
                      <td>
                        <div>
                          <div style={{ fontWeight: 500 }}>{role.name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{role.description}</div>
                        </div>
                      </td>
                      <td>{role.users}</td>
                      <td>{role.policies}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Events Page
// ========================================
function EventsPage() {
  const rules = [
    { 
      name: 'minio-to-workflow', 
      pattern: '{ source: "minio", detail-type: "ObjectCreated" }',
      targets: 'doc_ingest_workflow',
      status: 'Enabled',
      triggers: 234
    },
    { 
      name: 'notify-on-complete', 
      pattern: '{ source: "temporal", detail-type: "WorkflowCompleted" }',
      targets: 'send_notification',
      status: 'Enabled',
      triggers: 189
    },
    { 
      name: 'error-handler', 
      pattern: '{ source: "*", detail-type: "Error" }',
      targets: 'error_handler_fn',
      status: 'Disabled',
      triggers: 12
    },
  ]

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Event Rules</h1>
          <p className="page-description">Route events to workflows and functions</p>
        </div>
        <button className="btn btn-primary">
          <Plus size={16} />
          Create Rule
        </button>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Rule Name</th>
                <th>Event Pattern</th>
                <th>Targets</th>
                <th>Status</th>
                <th>Triggers</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule, i) => (
                <tr key={i}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div className="resource-icon topic">
                        <Zap size={14} />
                      </div>
                      <span className="code">{rule.name}</span>
                    </div>
                  </td>
                  <td><span className="code" style={{ fontSize: '11px' }}>{rule.pattern}</span></td>
                  <td><span className="code">{rule.targets}</span></td>
                  <td>
                    <span className={`status ${rule.status === 'Enabled' ? 'status-active' : 'status-pending'}`}>
                      <span className="status-dot"></span>
                      {rule.status}
                    </span>
                  </td>
                  <td>{rule.triggers}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Placeholder Pages
// ========================================
function PlaceholderPage({ title, description }) {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      <div className="card">
        <div className="empty-state">
          <Box size={48} />
          <h3>Coming Soon</h3>
          <p>This feature is under development</p>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Main App
// ========================================
function App() {
  const [activePage, setActivePage] = useState('dashboard')

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <DashboardPage />
      case 'functions': return <FunctionsPage />
      case 'buckets': return <BucketsPage />
      case 'workflows': return <WorkflowsPage />
      case 'iam': return <IAMPage />
      case 'events': return <EventsPage />
      case 'policies': return <PlaceholderPage title="Policies" description="Manage IAM policies" />
      case 'api-keys': return <PlaceholderPage title="API Keys" description="Manage programmatic access" />
      case 'topics': return <PlaceholderPage title="Topics" description="Manage message topics" />
      case 'logs': return <PlaceholderPage title="Logs" description="View application logs" />
      case 'metrics': return <PlaceholderPage title="Metrics" description="View system metrics" />
      default: return <DashboardPage />
    }
  }

  const getPageTitle = () => {
    const titles = {
      dashboard: 'Dashboard',
      functions: 'Functions',
      buckets: 'Buckets',
      workflows: 'Workflows',
      iam: 'IAM',
      events: 'Event Rules',
      policies: 'Policies',
      'api-keys': 'API Keys',
      topics: 'Topics',
      logs: 'Logs',
      metrics: 'Metrics',
    }
    return titles[activePage] || 'Dashboard'
  }

  return (
    <div className="app">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <main className="main">
        <Header title={getPageTitle()} />
        <div className="content">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}

export default App
