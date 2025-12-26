import React, { useState } from 'react'
import { Folder, Plus, Trash2, RefreshCw, HardDrive, FileCode, ExternalLink } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Table, Status, StatCard, ConfirmDialog, EmptyState } from '../components/ui'
import { PageLayout } from '../components/Layout'

export function BucketsPage() {
  const { data: buckets, loading, refetch } = useApi(() => api.getBuckets())
  const createModal = useToggle()
  const deleteModal = useToggle()
  const [newBucket, setNewBucket] = useState('')
  const [selectedBucket, setSelectedBucket] = useState(null)
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Stats
  const totalSize = buckets?.reduce((sum, b) => sum + (b.size_bytes || 0), 0) || 0
  const totalObjects = buckets?.reduce((sum, b) => sum + (b.object_count || 0), 0) || 0

  const handleCreate = async () => {
    if (!newBucket.trim()) return
    setCreating(true)
    try {
      await api.createBucket(api.defaultProjectId, newBucket.trim())
      setNewBucket('')
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error creating bucket: ' + e.message)
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!selectedBucket) return
    setDeleting(true)
    try {
      await api.deleteBucket(api.defaultProjectId, selectedBucket.name)
      deleteModal.setFalse()
      setSelectedBucket(null)
      refetch()
    } catch (e) {
      alert('Error deleting bucket: ' + e.message)
    }
    setDeleting(false)
  }

  const openDelete = (bucket) => {
    setSelectedBucket(bucket)
    deleteModal.setTrue()
  }

  const columns = [
    { 
      header: 'Name', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon bucket"><Folder size={14} /></div>
          <span className="code">{row.name}</span>
        </div>
      )
    },
    { header: 'Objects', key: 'object_count', render: row => row.object_count?.toLocaleString() || '0' },
    { header: 'Size', key: 'size_bytes', render: row => formatBytes(row.size_bytes || 0) },
    { header: 'Created', key: 'created_at', render: row => new Date(row.created_at).toLocaleDateString() },
    { header: 'Status', key: 'status', render: () => <Status status="Active" /> },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="secondary" icon={ExternalLink} onClick={() => window.open(`http://localhost:9001/browser/${row.name}`, '_blank')}>
            Browse
          </Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => openDelete(row)}>
            Delete
          </Button>
        </div>
      )
    },
  ]

  return (
    <PageLayout 
      title="Storage Buckets" 
      subtitle="S3-compatible object storage powered by MinIO"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Create Bucket</Button>
        </div>
      }
    >
      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <StatCard icon={Folder} label="Total Buckets" value={loading ? '...' : buckets?.length || 0} color="blue" />
        <StatCard icon={FileCode} label="Total Objects" value={loading ? '...' : totalObjects.toLocaleString()} color="purple" />
        <StatCard icon={HardDrive} label="Storage Used" value={loading ? '...' : formatBytes(totalSize)} color="green" />
      </div>

      {/* Buckets Table */}
      <Card>
        <Table columns={columns} data={buckets} loading={loading} emptyMessage="No buckets found. Create your first bucket!" />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Bucket"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} loading={creating} disabled={!newBucket.trim()}>
              Create Bucket
            </Button>
          </>
        }
      >
        <Input 
          label="Bucket Name" 
          value={newBucket} 
          onChange={e => setNewBucket(e.target.value)}
          placeholder="my-bucket"
        />
        <p className="form-help">Bucket names must be lowercase and can contain hyphens.</p>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={handleDelete}
        title="Delete Bucket"
        message={`Are you sure you want to delete bucket "${selectedBucket?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default BucketsPage
