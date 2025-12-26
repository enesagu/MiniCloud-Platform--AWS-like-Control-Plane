import React, { useState } from 'react'
import { Terminal, RefreshCw, Filter, Download, Search } from 'lucide-react'
import { useApi, useDebounce } from '../hooks'
import { api } from '../api'
import { Button, Card, Table, Input, Select } from '../components/ui'
import { PageLayout, SearchInput } from '../components/Layout'

export function AuditLogsPage() {
  const [filters, setFilters] = useState({ action: '', resource_type: '', actor: '' })
  const debouncedFilters = useDebounce(filters, 500)
  
  const { data: logs, loading, refetch } = useApi(
    () => api.getAuditLogs(api.defaultOrgId, debouncedFilters),
    [debouncedFilters]
  )

  const [search, setSearch] = useState('')

  const filteredLogs = logs?.filter(log => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      log.action?.toLowerCase().includes(searchLower) ||
      log.resource_type?.toLowerCase().includes(searchLower) ||
      log.actor_id?.toLowerCase().includes(searchLower) ||
      log.resource_id?.toLowerCase().includes(searchLower)
    )
  })

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Actor', 'Action', 'Resource Type', 'Resource ID', 'Status'].join(','),
      ...filteredLogs.map(log => [
        log.timestamp,
        log.actor_id,
        log.action,
        log.resource_type,
        log.resource_id,
        log.status
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
  }

  const columns = [
    { 
      header: 'Timestamp', 
      key: 'timestamp',
      render: row => (
        <span className="timestamp">
          {new Date(row.timestamp).toLocaleString()}
        </span>
      )
    },
    { 
      header: 'Actor', 
      key: 'actor_id',
      render: row => (
        <div className="actor-cell">
          <div className="avatar-sm">{row.actor_id?.[0]?.toUpperCase() || '?'}</div>
          <span>{row.actor_id || 'system'}</span>
        </div>
      )
    },
    { 
      header: 'Action', 
      key: 'action',
      render: row => {
        const actionClass = row.action?.includes('Delete') ? 'action-delete' :
                           row.action?.includes('Create') ? 'action-create' :
                           row.action?.includes('Update') ? 'action-update' : ''
        return <span className={`action-badge ${actionClass}`}>{row.action}</span>
      }
    },
    { header: 'Resource Type', key: 'resource_type' },
    { header: 'Resource ID', key: 'resource_id', render: row => <span className="code">{row.resource_id?.slice(0, 12)}...</span> },
    { 
      header: 'Status', 
      key: 'status',
      render: row => (
        <span className={`log-status ${row.status === 'success' ? 'success' : 'error'}`}>
          {row.status || 'success'}
        </span>
      )
    },
    { 
      header: 'IP', 
      key: 'ip_address',
      render: row => <span className="code">{row.ip_address || '-'}</span>
    },
  ]

  return (
    <PageLayout 
      title="Audit Logs" 
      subtitle="Complete activity trail for compliance and security"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={Download} onClick={handleExport} disabled={!filteredLogs?.length}>
            Export CSV
          </Button>
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
        </div>
      }
    >
      {/* Filters */}
      <Card className="filter-card">
        <div className="filter-row">
          <div className="search-wrapper">
            <Search size={16} />
            <input 
              type="text" 
              className="search-input"
              placeholder="Search logs..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <Select 
            label=""
            value={filters.resource_type}
            onChange={e => setFilters({...filters, resource_type: e.target.value})}
            options={[
              { value: '', label: 'All Resources' },
              { value: 'bucket', label: 'Buckets' },
              { value: 'function', label: 'Functions' },
              { value: 'workflow', label: 'Workflows' },
              { value: 'user', label: 'Users' },
              { value: 'policy', label: 'Policies' },
            ]}
          />
        </div>
      </Card>

      {/* Logs Table */}
      <Card>
        <div className="log-count">
          Showing {filteredLogs?.length || 0} logs
        </div>
        <Table 
          columns={columns} 
          data={filteredLogs} 
          loading={loading} 
          emptyMessage="No audit logs found"
        />
      </Card>
    </PageLayout>
  )
}

export default AuditLogsPage
