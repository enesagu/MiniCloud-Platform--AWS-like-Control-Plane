import React, { useState } from 'react'
import { Bell, Plus, Trash2, RefreshCw, Send, Users, Mail, Globe, Zap, MessageSquare } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Select, Table, Status, ConfirmDialog, Textarea, StatCard, CodeBlock } from '../components/ui'
import { PageLayout } from '../components/Layout'

const PROTOCOLS = [
  { value: 'http', label: 'HTTP' },
  { value: 'https', label: 'HTTPS' },
  { value: 'email', label: 'Email' },
  { value: 'sqs', label: 'Queue (SQS)' },
  { value: 'lambda', label: 'Function (Lambda)' },
]

export function TopicsPage() {
  const { data: topics, loading, refetch } = useApi(() => api.getTopics())
  const createModal = useToggle()
  const publishModal = useToggle()
  const subsModal = useToggle()
  const deleteModal = useToggle()
  const addSubModal = useToggle()
  
  const [form, setForm] = useState({ name: '', display_name: '', description: '' })
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [subscriptions, setSubscriptions] = useState([])
  const [loadingSubs, setLoadingSubs] = useState(false)
  const [publishForm, setPublishForm] = useState({ body: '', attributes: '{}' })
  const [subForm, setSubForm] = useState({ protocol: 'http', endpoint: '' })
  const [creating, setCreating] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await api.createTopic(api.defaultProjectId, form)
      setForm({ name: '', display_name: '', description: '' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!selectedTopic) return
    setDeleting(true)
    try {
      await api.deleteTopic(api.defaultProjectId, selectedTopic.id)
      deleteModal.setFalse()
      setSelectedTopic(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const handlePublish = async () => {
    if (!selectedTopic || !publishForm.body.trim()) return
    setPublishing(true)
    try {
      const attrs = JSON.parse(publishForm.attributes || '{}')
      const result = await api.publishToTopic(selectedTopic.id, { body: publishForm.body, attributes: attrs })
      alert(`Message published! Delivered to ${result.delivered_to} subscribers`)
      publishModal.setFalse()
      setPublishForm({ body: '', attributes: '{}' })
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setPublishing(false)
  }

  const openSubscriptions = async (topic) => {
    setSelectedTopic(topic)
    setLoadingSubs(true)
    subsModal.setTrue()
    try {
      const subs = await api.getSubscriptions(topic.id)
      setSubscriptions(subs)
    } catch {
      setSubscriptions([])
    }
    setLoadingSubs(false)
  }

  const handleAddSubscription = async () => {
    if (!selectedTopic || !subForm.endpoint.trim()) return
    try {
      await api.createSubscription(selectedTopic.id, subForm)
      setSubForm({ protocol: 'http', endpoint: '' })
      addSubModal.setFalse()
      // Refresh subscriptions
      const subs = await api.getSubscriptions(selectedTopic.id)
      setSubscriptions(subs)
    } catch (e) {
      alert('Error: ' + e.message)
    }
  }

  const handleDeleteSubscription = async (subId) => {
    try {
      await api.deleteSubscription(subId)
      const subs = await api.getSubscriptions(selectedTopic.id)
      setSubscriptions(subs)
    } catch (e) {
      alert('Error: ' + e.message)
    }
  }

  const openPublish = (topic) => {
    setSelectedTopic(topic)
    setPublishForm({ body: '', attributes: '{}' })
    publishModal.setTrue()
  }

  const openDelete = (topic) => {
    setSelectedTopic(topic)
    deleteModal.setTrue()
  }

  // Stats
  const totalMessages = topics?.reduce((sum, t) => sum + (t.message_count || 0), 0) || 0

  const columns = [
    { 
      header: 'Topic', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon topic"><Bell size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            {row.description && <div className="text-muted">{row.description}</div>}
          </div>
        </div>
      )
    },
    { 
      header: 'ARN', 
      key: 'arn',
      render: row => <span className="code text-sm">arn:minicloud:sns:proj-default:{row.name}</span>
    },
    { header: 'Messages', key: 'message_count', render: row => (row.message_count || 0).toLocaleString() },
    { header: 'Created', key: 'created_at', render: row => new Date(row.created_at).toLocaleDateString() },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="primary" icon={Send} onClick={() => openPublish(row)}>Publish</Button>
          <Button size="sm" variant="secondary" icon={Users} onClick={() => openSubscriptions(row)}>Subs</Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => openDelete(row)}>Delete</Button>
        </div>
      )
    },
  ]

  const subColumns = [
    { header: 'Protocol', key: 'protocol', render: row => <span className="code">{row.protocol}</span> },
    { header: 'Endpoint', key: 'endpoint', render: row => <span className="code text-sm">{row.endpoint}</span> },
    { header: 'Status', key: 'status', render: row => <Status status={row.status} /> },
    { header: 'Deliveries', key: 'delivery_count', render: row => row.delivery_count || 0 },
    { 
      header: 'Actions',
      key: 'actions',
      render: row => (
        <Button size="sm" variant="danger" icon={Trash2} onClick={() => handleDeleteSubscription(row.id)}>Remove</Button>
      )
    },
  ]

  return (
    <PageLayout 
      title="Topics (SNS)" 
      subtitle="Pub/Sub messaging for fan-out notifications"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Topic</Button>
        </div>
      }
    >
      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <StatCard icon={Bell} label="Total Topics" value={loading ? '...' : topics?.length || 0} color="purple" />
        <StatCard icon={MessageSquare} label="Messages Published" value={loading ? '...' : totalMessages.toLocaleString()} color="blue" />
        <StatCard icon={Users} label="Active Subscriptions" value="-" color="green" />
      </div>

      <Card>
        <Table columns={columns} data={topics} loading={loading} emptyMessage="No topics. Create your first topic!" />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Topic"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create</Button>
          </>
        }
      >
        <Input label="Topic Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="my-notifications" />
        <Input label="Display Name" value={form.display_name} onChange={e => setForm({...form, display_name: e.target.value})} placeholder="My Notifications" />
        <Textarea label="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={2} />
      </Modal>

      {/* Publish Modal */}
      <Modal 
        open={publishModal.value} 
        onClose={publishModal.setFalse} 
        title={`Publish to: ${selectedTopic?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={publishModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Send} onClick={handlePublish} loading={publishing}>Publish</Button>
          </>
        }
      >
        <Textarea label="Message Body" value={publishForm.body} onChange={e => setPublishForm({...publishForm, body: e.target.value})} rows={5} placeholder="Enter your message..." />
        <Textarea label="Attributes (JSON)" value={publishForm.attributes} onChange={e => setPublishForm({...publishForm, attributes: e.target.value})} rows={3} />
      </Modal>

      {/* Subscriptions Modal */}
      <Modal 
        open={subsModal.value} 
        onClose={subsModal.setFalse} 
        title={`Subscriptions: ${selectedTopic?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={subsModal.setFalse}>Close</Button>
            <Button variant="primary" icon={Plus} onClick={addSubModal.setTrue}>Add Subscription</Button>
          </>
        }
      >
        <Table columns={subColumns} data={subscriptions} loading={loadingSubs} emptyMessage="No subscriptions" />
      </Modal>

      {/* Add Subscription Modal */}
      <Modal 
        open={addSubModal.value} 
        onClose={addSubModal.setFalse} 
        title="Add Subscription"
        footer={
          <>
            <Button variant="secondary" onClick={addSubModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleAddSubscription}>Subscribe</Button>
          </>
        }
      >
        <Select label="Protocol" value={subForm.protocol} onChange={e => setSubForm({...subForm, protocol: e.target.value})} options={PROTOCOLS} />
        <Input 
          label="Endpoint" 
          value={subForm.endpoint} 
          onChange={e => setSubForm({...subForm, endpoint: e.target.value})} 
          placeholder={subForm.protocol === 'email' ? 'user@example.com' : 'https://example.com/webhook'}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Topic"
        message={`Are you sure you want to delete topic "${selectedTopic?.name}" and all its subscriptions?`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default TopicsPage
