import React, { useState } from 'react'
import { Zap, Plus, Trash2, RefreshCw, ToggleLeft, ToggleRight, Edit } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Table, Status, ConfirmDialog, Textarea, Select } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function EventRulesPage() {
  const { data: rules, loading, refetch } = useApi(() => api.getEventRules())
  const createModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({ 
    name: '', 
    event_pattern: '{\n  "source": ["minio"],\n  "detail-type": ["ObjectCreated"]\n}',
    target_type: 'workflow',
    target_name: ''
  })
  const [selectedRule, setSelectedRule] = useState(null)
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim() || !form.target_name.trim()) return
    setCreating(true)
    try {
      const eventPattern = JSON.parse(form.event_pattern)
      await api.createEventRule(api.defaultProjectId, {
        name: form.name,
        event_pattern: eventPattern,
        targets: [{ type: form.target_type, name: form.target_name }],
        enabled: true
      })
      setForm({ name: '', event_pattern: '{}', target_type: 'workflow', target_name: '' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!selectedRule) return
    setDeleting(true)
    try {
      await api.deleteEventRule(api.defaultProjectId, selectedRule.id)
      deleteModal.setFalse()
      setSelectedRule(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const columns = [
    { 
      header: 'Rule Name', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon topic"><Zap size={14} /></div>
          <span className="code">{row.name}</span>
        </div>
      )
    },
    { 
      header: 'Event Pattern', 
      key: 'event_pattern',
      render: row => (
        <span className="code text-sm" style={{ maxWidth: 300, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {JSON.stringify(row.event_pattern)}
        </span>
      )
    },
    { 
      header: 'Targets', 
      key: 'targets',
      render: row => row.targets?.map((t, i) => (
        <span key={i} className="code">{t.type}:{t.name}</span>
      )) || '-'
    },
    { 
      header: 'Status', 
      key: 'enabled',
      render: row => (
        <div className="toggle-status">
          {row.enabled ? <ToggleRight size={20} className="text-success"/> : <ToggleLeft size={20} className="text-muted"/>}
          <Status status={row.enabled ? 'Enabled' : 'Disabled'} />
        </div>
      )
    },
    { header: 'Triggers', key: 'trigger_count', render: row => row.trigger_count || 0 },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => { setSelectedRule(row); deleteModal.setTrue(); }}>
            Delete
          </Button>
        </div>
      )
    },
  ]

  return (
    <PageLayout 
      title="Event Rules" 
      subtitle="Route events to workflows and functions (EventBridge-style)"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Rule</Button>
        </div>
      }
    >
      <Card>
        <Table columns={columns} data={rules} loading={loading} emptyMessage="No event rules configured." />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Event Rule"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create Rule</Button>
          </>
        }
      >
        <Input 
          label="Rule Name" 
          value={form.name} 
          onChange={e => setForm({...form, name: e.target.value})} 
          placeholder="minio-to-workflow"
        />
        <Textarea 
          label="Event Pattern (JSON)" 
          value={form.event_pattern} 
          onChange={e => setForm({...form, event_pattern: e.target.value})} 
          rows={6}
        />
        <div className="grid-2">
          <Select 
            label="Target Type" 
            value={form.target_type} 
            onChange={e => setForm({...form, target_type: e.target.value})}
            options={['workflow', 'function', 'queue']}
          />
          <Input 
            label="Target Name" 
            value={form.target_name} 
            onChange={e => setForm({...form, target_name: e.target.value})} 
            placeholder="doc_ingest_workflow"
          />
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Event Rule"
        message={`Are you sure you want to delete rule "${selectedRule?.name}"?`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default EventRulesPage
