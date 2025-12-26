import React, { useState } from 'react'
import { Code, Plus, Trash2, RefreshCw, Play, Clock, Cpu, Settings } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Select, Table, Status, ConfirmDialog, CodeBlock, Tabs } from '../components/ui'
import { PageLayout } from '../components/Layout'

const RUNTIMES = ['python3.10', 'python3.9', 'nodejs18.x', 'nodejs16.x', 'go1.x', 'java11']
const MEMORY_OPTIONS = [128, 256, 512, 1024, 2048]

export function FunctionsPage() {
  const { data: functions, loading, refetch } = useApi(() => api.getFunctions())
  const createModal = useToggle()
  const invokeModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({ name: '', runtime: 'python3.10', memory: 128, timeout: 30, handler: 'main.handler' })
  const [selectedFn, setSelectedFn] = useState(null)
  const [invokePayload, setInvokePayload] = useState('{}')
  const [invokeResult, setInvokeResult] = useState(null)
  const [creating, setCreating] = useState(false)
  const [invoking, setInvoking] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const updateForm = (key, value) => setForm({ ...form, [key]: value })

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await api.createFunction(api.defaultProjectId, form)
      setForm({ name: '', runtime: 'python3.10', memory: 128, timeout: 30, handler: 'main.handler' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleInvoke = async () => {
    if (!selectedFn) return
    setInvoking(true)
    setInvokeResult(null)
    try {
      const payload = JSON.parse(invokePayload || '{}')
      const result = await api.invokeFunction(selectedFn.id, payload)
      setInvokeResult(result)
    } catch (e) {
      setInvokeResult({ error: e.message })
    }
    setInvoking(false)
  }

  const handleDelete = async () => {
    if (!selectedFn) return
    setDeleting(true)
    try {
      await api.deleteFunction(api.defaultProjectId, selectedFn.id)
      deleteModal.setFalse()
      setSelectedFn(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const openInvoke = (fn) => {
    setSelectedFn(fn)
    setInvokePayload('{}')
    setInvokeResult(null)
    invokeModal.setTrue()
  }

  const openDelete = (fn) => {
    setSelectedFn(fn)
    deleteModal.setTrue()
  }

  const columns = [
    { 
      header: 'Name', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon function"><Code size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            <div className="text-muted">{row.spec?.handler || 'main.handler'}</div>
          </div>
        </div>
      )
    },
    { header: 'Runtime', key: 'runtime', render: row => <span className="code">{row.spec?.runtime || 'python3.10'}</span> },
    { header: 'Memory', key: 'memory', render: row => `${row.spec?.memory_mb || 128} MB` },
    { header: 'Timeout', key: 'timeout', render: row => `${row.spec?.timeout_seconds || 30}s` },
    { header: 'Status', key: 'status', render: row => <Status status={row.state?.status || 'Active'} /> },
    { header: 'Invocations', key: 'invocations', render: row => (row.state?.invocation_count || 0).toLocaleString() },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="primary" icon={Play} onClick={() => openInvoke(row)}>Invoke</Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => openDelete(row)}>Delete</Button>
        </div>
      )
    },
  ]

  return (
    <PageLayout 
      title="Functions" 
      subtitle="Deploy and manage serverless functions"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Function</Button>
        </div>
      }
    >
      <Card>
        <Table columns={columns} data={functions} loading={loading} emptyMessage="No functions deployed. Create your first function!" />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Function"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create Function</Button>
          </>
        }
      >
        <div className="form-row">
          <Input label="Function Name" value={form.name} onChange={e => updateForm('name', e.target.value)} placeholder="my-function" />
        </div>
        <div className="form-row">
          <Select label="Runtime" value={form.runtime} onChange={e => updateForm('runtime', e.target.value)} options={RUNTIMES} />
        </div>
        <div className="grid-2">
          <Select label="Memory" value={form.memory} onChange={e => updateForm('memory', +e.target.value)} 
            options={MEMORY_OPTIONS.map(m => ({ value: m, label: `${m} MB` }))} />
          <Input label="Timeout (seconds)" type="number" value={form.timeout} onChange={e => updateForm('timeout', +e.target.value)} />
        </div>
        <Input label="Handler" value={form.handler} onChange={e => updateForm('handler', e.target.value)} placeholder="main.handler" />
      </Modal>

      {/* Invoke Modal */}
      <Modal 
        open={invokeModal.value} 
        onClose={invokeModal.setFalse} 
        title={`Invoke: ${selectedFn?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={invokeModal.setFalse}>Close</Button>
            <Button variant="primary" icon={Play} onClick={handleInvoke} loading={invoking}>Invoke</Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Request Payload (JSON)</label>
          <textarea 
            className="form-input code-input" 
            value={invokePayload} 
            onChange={e => setInvokePayload(e.target.value)}
            rows={5}
          />
        </div>
        {invokeResult && (
          <div className="form-group">
            <label className="form-label">Response</label>
            <CodeBlock code={invokeResult} />
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Function"
        message={`Are you sure you want to delete function "${selectedFn?.name}"?`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default FunctionsPage
