import React, { useState } from 'react'
import { Inbox, Plus, Trash2, RefreshCw, Send, Download, Eye, Package, Clock, Zap } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Table, Status, ConfirmDialog, Textarea, StatCard, CodeBlock } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function QueuesPage() {
  const { data: queues, loading, refetch } = useApi(() => api.getQueues())
  const createModal = useToggle()
  const sendModal = useToggle()
  const receiveModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({ name: '', description: '', visibility_timeout: 30, delay_seconds: 0 })
  const [selectedQueue, setSelectedQueue] = useState(null)
  const [sendForm, setSendForm] = useState({ body: '', attributes: '{}', delay_seconds: 0 })
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [creating, setCreating] = useState(false)
  const [sending, setSending] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [purging, setPurging] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await api.createQueue(api.defaultProjectId, form)
      setForm({ name: '', description: '', visibility_timeout: 30, delay_seconds: 0 })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!selectedQueue) return
    setDeleting(true)
    try {
      await api.deleteQueue(api.defaultProjectId, selectedQueue.id)
      deleteModal.setFalse()
      setSelectedQueue(null)
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setDeleting(false)
  }

  const handleSend = async () => {
    if (!selectedQueue || !sendForm.body.trim()) return
    setSending(true)
    try {
      const attrs = JSON.parse(sendForm.attributes || '{}')
      await api.sendMessage(selectedQueue.id, { 
        body: sendForm.body, 
        attributes: attrs,
        delay_seconds: sendForm.delay_seconds 
      })
      alert('Message sent!')
      setSendForm({ body: '', attributes: '{}', delay_seconds: 0 })
      sendModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setSending(false)
  }

  const handleReceive = async (queue) => {
    setSelectedQueue(queue)
    setLoadingMessages(true)
    receiveModal.setTrue()
    try {
      const result = await api.receiveMessages(queue.id, 10)
      setMessages(result.messages || [])
    } catch {
      setMessages([])
    }
    setLoadingMessages(false)
  }

  const handleDeleteMessage = async (receiptHandle) => {
    if (!selectedQueue) return
    try {
      await api.deleteMessage(selectedQueue.id, receiptHandle)
      // Refresh messages
      const result = await api.receiveMessages(selectedQueue.id, 10)
      setMessages(result.messages || [])
    } catch (e) {
      alert('Error: ' + e.message)
    }
  }

  const handlePurge = async () => {
    if (!selectedQueue) return
    setPurging(true)
    try {
      const result = await api.purgeQueue(selectedQueue.id)
      alert(`Purged ${result.deleted_count} messages`)
      setMessages([])
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setPurging(false)
  }

  const openSend = (queue) => {
    setSelectedQueue(queue)
    setSendForm({ body: '', attributes: '{}', delay_seconds: 0 })
    sendModal.setTrue()
  }

  const openDelete = (queue) => {
    setSelectedQueue(queue)
    deleteModal.setTrue()
  }

  // Stats
  const totalMessages = queues?.reduce((sum, q) => sum + (q.message_count || 0), 0) || 0
  const totalReceives = queues?.reduce((sum, q) => sum + (q.receive_count || 0), 0) || 0

  const columns = [
    { 
      header: 'Queue', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon queue"><Inbox size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            {row.description && <div className="text-muted">{row.description}</div>}
          </div>
        </div>
      )
    },
    { 
      header: 'URL', 
      key: 'url',
      render: row => <span className="code text-sm">sqs://minicloud/{row.name}</span>
    },
    { header: 'Messages', key: 'message_count', render: row => (row.message_count || 0).toLocaleString() },
    { header: 'Visibility', key: 'visibility_timeout', render: row => `${row.visibility_timeout || 30}s` },
    { header: 'Delay', key: 'delay_seconds', render: row => `${row.delay_seconds || 0}s` },
    { header: 'Created', key: 'created_at', render: row => new Date(row.created_at).toLocaleDateString() },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="primary" icon={Send} onClick={() => openSend(row)}>Send</Button>
          <Button size="sm" variant="secondary" icon={Download} onClick={() => handleReceive(row)}>Receive</Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => openDelete(row)}>Delete</Button>
        </div>
      )
    },
  ]

  const messageColumns = [
    { header: 'ID', key: 'id', render: row => <span className="code">{row.id?.slice(0, 8)}...</span> },
    { 
      header: 'Body', 
      key: 'body',
      render: row => (
        <div className="message-body" title={row.body}>
          {row.body?.slice(0, 50)}{row.body?.length > 50 ? '...' : ''}
        </div>
      )
    },
    { header: 'Sent', key: 'sent_at', render: row => new Date(row.sent_at).toLocaleString() },
    { header: 'Receives', key: 'receive_count', render: row => row.receive_count || 0 },
    { 
      header: 'Actions',
      key: 'actions',
      render: row => (
        <Button size="sm" variant="danger" icon={Trash2} onClick={() => handleDeleteMessage(row.receipt_handle)}>
          Delete
        </Button>
      )
    },
  ]

  return (
    <PageLayout 
      title="Queues (SQS)" 
      subtitle="Message queues for decoupled processing"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Queue</Button>
        </div>
      }
    >
      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <StatCard icon={Inbox} label="Total Queues" value={loading ? '...' : queues?.length || 0} color="blue" />
        <StatCard icon={Package} label="Messages in Queue" value={loading ? '...' : totalMessages.toLocaleString()} color="purple" />
        <StatCard icon={Download} label="Total Receives" value={loading ? '...' : totalReceives.toLocaleString()} color="green" />
        <StatCard icon={Clock} label="Avg Visibility" value="30s" color="yellow" />
      </div>

      <Card>
        <Table columns={columns} data={queues} loading={loading} emptyMessage="No queues. Create your first queue!" />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Queue"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating}>Create</Button>
          </>
        }
      >
        <Input label="Queue Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="my-queue" />
        <Textarea label="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={2} />
        <div className="grid-2">
          <Input label="Visibility Timeout (sec)" type="number" value={form.visibility_timeout} onChange={e => setForm({...form, visibility_timeout: +e.target.value})} />
          <Input label="Delay Seconds" type="number" value={form.delay_seconds} onChange={e => setForm({...form, delay_seconds: +e.target.value})} />
        </div>
      </Modal>

      {/* Send Message Modal */}
      <Modal 
        open={sendModal.value} 
        onClose={sendModal.setFalse} 
        title={`Send Message: ${selectedQueue?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={sendModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Send} onClick={handleSend} loading={sending}>Send Message</Button>
          </>
        }
      >
        <Textarea label="Message Body" value={sendForm.body} onChange={e => setSendForm({...sendForm, body: e.target.value})} rows={5} placeholder="Enter message content..." />
        <Textarea label="Attributes (JSON)" value={sendForm.attributes} onChange={e => setSendForm({...sendForm, attributes: e.target.value})} rows={3} />
        <Input label="Delay Seconds" type="number" value={sendForm.delay_seconds} onChange={e => setSendForm({...sendForm, delay_seconds: +e.target.value})} />
      </Modal>

      {/* Receive Messages Modal */}
      <Modal 
        open={receiveModal.value} 
        onClose={receiveModal.setFalse} 
        title={`Messages: ${selectedQueue?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="danger" onClick={handlePurge} loading={purging}>Purge All</Button>
            <Button variant="secondary" onClick={receiveModal.setFalse}>Close</Button>
          </>
        }
      >
        <Table columns={messageColumns} data={messages} loading={loadingMessages} emptyMessage="No messages in queue" />
        <p className="form-help" style={{ marginTop: '16px' }}>
          Messages are temporarily invisible after being received. Delete them to acknowledge processing.
        </p>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Queue"
        message={`Are you sure you want to delete queue "${selectedQueue?.name}" and all its messages?`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default QueuesPage
