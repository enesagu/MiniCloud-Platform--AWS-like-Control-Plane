import React from 'react'
import { Code, Folder, GitBranch, BarChart3, Activity, CheckCircle2, ArrowUpRight, Box, Zap } from 'lucide-react'
import { useApi } from '../hooks'
import { api } from '../api'
import { Card, StatCard, Table, Status } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function DashboardPage() {
  const { data: resources, loading: loadingResources } = useApi(() => api.getResources())
  const { data: auditLogs, loading: loadingLogs } = useApi(() => api.getAuditLogs())
  const { data: usage } = useApi(() => api.getUsage())

  // Count resources by type
  const counts = resources ? {
    functions: resources.filter(r => r.type === 'function').length,
    buckets: resources.filter(r => r.type === 'bucket').length,
    workflows: resources.filter(r => r.type === 'workflow').length,
    eventRules: resources.filter(r => r.type === 'event_rule').length,
  } : { functions: 0, buckets: 0, workflows: 0, eventRules: 0 }

  const stats = [
    { icon: Code, label: 'Functions', value: counts.functions, color: 'purple', trend: 'up', change: '+2 this week' },
    { icon: Folder, label: 'Buckets', value: counts.buckets, color: 'blue', trend: 'up', change: '+1 this week' },
    { icon: GitBranch, label: 'Workflows', value: counts.workflows, color: 'green' },
    { icon: Zap, label: 'Event Rules', value: counts.eventRules, color: 'yellow' },
  ]

  const activityColumns = [
    { header: 'Action', key: 'action', render: row => <span className="code">{row.action}</span> },
    { header: 'Resource', key: 'resource_type' },
    { header: 'Actor', key: 'actor_id' },
    { header: 'Time', key: 'timestamp', render: row => new Date(row.timestamp).toLocaleString() },
  ]

  const resourceColumns = [
    { header: 'Name', key: 'name', render: row => (
      <div className="resource-name">
        <div className={`resource-icon ${row.type}`}>
          {row.type === 'bucket' ? <Folder size={14}/> : row.type === 'function' ? <Code size={14}/> : <GitBranch size={14}/>}
        </div>
        <span className="code">{row.name}</span>
      </div>
    )},
    { header: 'Type', key: 'type' },
    { header: 'Status', key: 'status', render: row => <Status status={row.state?.status || 'Active'} /> },
  ]

  return (
    <PageLayout title="Dashboard" subtitle="Overview of your MiniCloud resources and activity">
      {/* Stats Grid */}
      <div className="stats-grid">
        {stats.map((stat, i) => (
          <StatCard key={i} {...stat} value={loadingResources ? '...' : stat.value} />
        ))}
      </div>

      {/* Usage Stats */}
      {usage && (
        <div className="usage-banner">
          <div className="usage-item">
            <span className="usage-label">API Calls (24h)</span>
            <span className="usage-value">{usage.api_calls_24h?.toLocaleString() || 0}</span>
          </div>
          <div className="usage-item">
            <span className="usage-label">Storage Used</span>
            <span className="usage-value">{usage.storage_bytes ? (usage.storage_bytes / 1024 / 1024).toFixed(2) + ' MB' : '0 MB'}</span>
          </div>
          <div className="usage-item">
            <span className="usage-label">Function Invocations</span>
            <span className="usage-value">{usage.function_invocations?.toLocaleString() || 0}</span>
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Recent Activity */}
        <Card title="Recent Activity" icon={Activity}>
          <Table 
            columns={activityColumns} 
            data={auditLogs?.slice(0, 5)} 
            loading={loadingLogs}
            emptyMessage="No recent activity"
          />
        </Card>

        {/* Resources */}
        <Card title="Resources" icon={Box}>
          <Table 
            columns={resourceColumns} 
            data={resources?.slice(0, 5)} 
            loading={loadingResources}
            emptyMessage="No resources found"
          />
        </Card>
      </div>
    </PageLayout>
  )
}

export default DashboardPage
