import React, { useState } from 'react'
import { Shield, Users, FileText, Plus, Trash2, RefreshCw, Key, UserPlus, Edit } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Table, Status, ConfirmDialog, Textarea, Tabs, CodeBlock } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function IAMPage() {
  const [activeTab, setActiveTab] = useState('users')
  
  const tabs = [
    { id: 'users', label: 'Users', icon: Users },
    { id: 'policies', label: 'Policies', icon: FileText },
    { id: 'simulate', label: 'Policy Simulator', icon: Shield },
  ]

  return (
    <PageLayout title="Identity & Access Management" subtitle="Manage users, policies, and permissions">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
      <div className="tab-content">
        {activeTab === 'users' && <UsersTab />}
        {activeTab === 'policies' && <PoliciesTab />}
        {activeTab === 'simulate' && <SimulatorTab />}
      </div>
    </PageLayout>
  )
}

// Users Tab
function UsersTab() {
  const { data: users, loading, refetch } = useApi(() => api.getUsers())
  const createModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [selectedUser, setSelectedUser] = useState(null)
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleCreate = async () => {
    if (!form.username.trim() || !form.email.trim()) return
    setCreating(true)
    try {
      await api.createUser(api.defaultOrgId, form)
      setForm({ username: '', email: '', password: '' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!selectedUser) return
    setDeleting(true)
    try {
      await api.deleteUser(api.defaultOrgId, selectedUser.id)
      deleteModal.setFalse()
      setSelectedUser(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const columns = [
    { 
      header: 'User', 
      key: 'username',
      render: row => (
        <div className="user-info">
          <div className="avatar">{row.username?.[0]?.toUpperCase() || 'U'}</div>
          <div>
            <span className="user-name">{row.username}</span>
            <span className="user-email">{row.email}</span>
          </div>
        </div>
      )
    },
    { header: 'Created', key: 'created_at', render: row => new Date(row.created_at).toLocaleDateString() },
    { header: 'Status', key: 'status', render: () => <Status status="Active" /> },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => { setSelectedUser(row); deleteModal.setTrue(); }}>
            Delete
          </Button>
        </div>
      )
    },
  ]

  return (
    <Card 
      title="Users" 
      icon={Users}
      action={
        <div className="button-group">
          <Button size="sm" variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button size="sm" variant="primary" icon={UserPlus} onClick={createModal.setTrue}>Add User</Button>
        </div>
      }
    >
      <Table columns={columns} data={users} loading={loading} emptyMessage="No users found" />

      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Add User"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Add User</Button>
          </>
        }
      >
        <Input label="Username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
        <Input label="Email" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
        <Input label="Password" type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
      </Modal>

      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete User"
        message={`Are you sure you want to delete user "${selectedUser?.username}"?`}
        confirmText="Delete"
        loading={deleting}
      />
    </Card>
  )
}

// Policies Tab
function PoliciesTab() {
  const { data: policies, loading, refetch } = useApi(() => api.getPolicies())
  const createModal = useToggle()
  const viewModal = useToggle()
  
  const [form, setForm] = useState({ 
    name: '', 
    description: '',
    document: JSON.stringify({
      Version: "2024-01-01",
      Statement: [{
        Effect: "Allow",
        Action: ["*"],
        Resource: ["*"]
      }]
    }, null, 2)
  })
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      const document = JSON.parse(form.document)
      await api.createPolicy(api.defaultOrgId, { name: form.name, description: form.description, document })
      setForm({ name: '', description: '', document: '{}' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const columns = [
    { header: 'Name', key: 'name', render: row => <span className="code">{row.name}</span> },
    { header: 'Description', key: 'description' },
    { header: 'Created', key: 'created_at', render: row => new Date(row.created_at).toLocaleDateString() },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <Button size="sm" variant="secondary" onClick={() => { setSelectedPolicy(row); viewModal.setTrue(); }}>
          View
        </Button>
      )
    },
  ]

  return (
    <Card 
      title="Policies" 
      icon={FileText}
      action={
        <div className="button-group">
          <Button size="sm" variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button size="sm" variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Policy</Button>
        </div>
      }
    >
      <Table columns={columns} data={policies} loading={loading} emptyMessage="No policies found" />

      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Policy"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create</Button>
          </>
        }
      >
        <Input label="Policy Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="MyPolicy" />
        <Input label="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
        <Textarea label="Policy Document (JSON)" value={form.document} onChange={e => setForm({...form, document: e.target.value})} rows={10} />
      </Modal>

      <Modal 
        open={viewModal.value} 
        onClose={viewModal.setFalse} 
        title={`Policy: ${selectedPolicy?.name}`}
        size="lg"
        footer={<Button variant="secondary" onClick={viewModal.setFalse}>Close</Button>}
      >
        <p><strong>Description:</strong> {selectedPolicy?.description}</p>
        <CodeBlock code={selectedPolicy?.document || {}} />
      </Modal>
    </Card>
  )
}

// Policy Simulator Tab
function SimulatorTab() {
  const [action, setAction] = useState('minio:GetObject')
  const [resource, setResource] = useState('bucket:my-bucket/*')
  const [context, setContext] = useState('{}')
  const [result, setResult] = useState(null)
  const [simulating, setSimulating] = useState(false)

  const handleSimulate = async () => {
    setSimulating(true)
    try {
      const ctx = JSON.parse(context || '{}')
      const res = await api.simulatePolicy(action, resource, ctx)
      setResult(res)
    } catch (e) {
      setResult({ error: e.message })
    }
    setSimulating(false)
  }

  return (
    <Card title="Policy Simulator" icon={Shield}>
      <p className="card-description">Test if an action would be allowed or denied based on your policies.</p>
      
      <div className="grid-2">
        <Input label="Action" value={action} onChange={e => setAction(e.target.value)} placeholder="minio:GetObject" />
        <Input label="Resource" value={resource} onChange={e => setResource(e.target.value)} placeholder="bucket:my-bucket/*" />
      </div>
      <Textarea label="Context (JSON)" value={context} onChange={e => setContext(e.target.value)} rows={3} />
      
      <div className="simulator-actions">
        <Button variant="primary" icon={Shield} onClick={handleSimulate} loading={simulating}>Simulate</Button>
      </div>

      {result && (
        <div className={`simulation-result ${result.allowed ? 'allowed' : 'denied'}`}>
          <h4>{result.allowed ? '✅ ALLOWED' : '❌ DENIED'}</h4>
          {result.reason && <p>{result.reason}</p>}
          {result.matched_statement && <CodeBlock code={result.matched_statement} />}
        </div>
      )}
    </Card>
  )
}

export default IAMPage
