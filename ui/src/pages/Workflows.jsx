import React, { useState } from 'react'
import { GitBranch, Plus, Trash2, RefreshCw, Play, Clock, ExternalLink, CheckCircle, XCircle, Loader } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Table, Status, ConfirmDialog, CodeBlock, Textarea } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function WorkflowsPage() {
  const { data: workflows, loading, refetch } = useApi(() => api.getWorkflows())
  const createModal = useToggle()
  const startModal = useToggle()
  const runsModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({ name: '', definition: '' })
  const [selectedWf, setSelectedWf] = useState(null)
  const [startInput, setStartInput] = useState('{}')
  const [runs, setRuns] = useState([])
  const [creating, setCreating] = useState(false)
  const [starting, setStarting] = useState(false)
  const [loadingRuns, setLoadingRuns] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      const definition = form.definition ? JSON.parse(form.definition) : {}
      await api.createWorkflow(api.defaultProjectId, { name: form.name, definition })
      setForm({ name: '', definition: '' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleStart = async () => {
    if (!selectedWf) return
    setStarting(true)
    try {
      const input = JSON.parse(startInput || '{}')
      await api.startWorkflow(selectedWf.name, input)
      startModal.setFalse()
      alert('Workflow started successfully!')
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setStarting(false)
  }

  const handleDelete = async () => {
    if (!selectedWf) return
    setDeleting(true)
    try {
      await api.deleteWorkflow(api.defaultProjectId, selectedWf.id)
      deleteModal.setFalse()
      setSelectedWf(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const openStart = (wf) => {
    setSelectedWf(wf)
    setStartInput('{}')
    startModal.setTrue()
  }

  const openRuns = async (wf) => {
    setSelectedWf(wf)
    setLoadingRuns(true)
    runsModal.setTrue()
    try {
      const result = await api.getWorkflowRuns(wf.name)
      setRuns(result || [])
    } catch {
      setRuns([])
    }
    setLoadingRuns(false)
  }

  const openDelete = (wf) => {
    setSelectedWf(wf)
    deleteModal.setTrue()
  }

  const columns = [
    { 
      header: 'Name', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon workflow"><GitBranch size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            <div className="text-muted">Created: {new Date(row.created_at).toLocaleDateString()}</div>
          </div>
        </div>
      )
    },
    { header: 'Total Runs', key: 'runs', render: row => row.state?.run_count || 0 },
    { header: 'Last Run', key: 'last_run', render: row => row.state?.last_run_at ? new Date(row.state.last_run_at).toLocaleString() : 'Never' },
    { header: 'Status', key: 'status', render: row => <Status status={row.state?.status || 'Active'} /> },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="primary" icon={Play} onClick={() => openStart(row)}>Start</Button>
          <Button size="sm" variant="secondary" icon={Clock} onClick={() => openRuns(row)}>Runs</Button>
          <Button size="sm" variant="secondary" icon={ExternalLink} onClick={() => window.open('http://localhost:8080', '_blank')}>
            Temporal
          </Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => openDelete(row)}>Delete</Button>
        </div>
      )
    },
  ]

  const runColumns = [
    { header: 'Run ID', key: 'run_id', render: row => <span className="code">{row.run_id?.slice(0, 8)}...</span> },
    { header: 'Status', key: 'status', render: row => {
      const icon = row.status === 'COMPLETED' ? <CheckCircle size={14} className="text-success"/> : 
                   row.status === 'RUNNING' ? <Loader size={14} className="text-info spinning"/> :
                   row.status === 'FAILED' ? <XCircle size={14} className="text-danger"/> : null
      return <span className="run-status">{icon} {row.status}</span>
    }},
    { header: 'Started', key: 'start_time', render: row => new Date(row.start_time).toLocaleString() },
    { header: 'Duration', key: 'duration', render: row => row.duration || '-' },
  ]

  return (
    <PageLayout 
      title="Workflows" 
      subtitle="Durable workflow orchestration powered by Temporal"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={ExternalLink} onClick={() => window.open('http://localhost:8080', '_blank')}>
            Temporal UI
          </Button>
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Workflow</Button>
        </div>
      }
    >
      <Card>
        <Table columns={columns} data={workflows} loading={loading} emptyMessage="No workflows registered." />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Workflow"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create</Button>
          </>
        }
      >
        <Input label="Workflow Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="my-workflow" />
        <Textarea label="Definition (JSON, optional)" value={form.definition} onChange={e => setForm({...form, definition: e.target.value})} placeholder="{}" rows={5} />
      </Modal>

      {/* Start Modal */}
      <Modal 
        open={startModal.value} 
        onClose={startModal.setFalse} 
        title={`Start Workflow: ${selectedWf?.name}`}
        footer={
          <>
            <Button variant="secondary" onClick={startModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Play} onClick={handleStart} loading={starting}>Start</Button>
          </>
        }
      >
        <Textarea label="Input (JSON)" value={startInput} onChange={e => setStartInput(e.target.value)} rows={5} />
      </Modal>

      {/* Runs Modal */}
      <Modal 
        open={runsModal.value} 
        onClose={runsModal.setFalse} 
        title={`Runs: ${selectedWf?.name}`}
        size="lg"
        footer={<Button variant="secondary" onClick={runsModal.setFalse}>Close</Button>}
      >
        <Table columns={runColumns} data={runs} loading={loadingRuns} emptyMessage="No runs found" />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Workflow"
        message={`Are you sure you want to delete workflow "${selectedWf?.name}"?`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default WorkflowsPage
