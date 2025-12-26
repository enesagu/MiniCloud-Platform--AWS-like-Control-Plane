import React, { useState } from 'react'
import { Server, Plus, Trash2, RefreshCw, Play, Square, RotateCcw, Power, Monitor, Cpu, HardDrive, Network, Activity, Clock } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Select, Table, Status, ConfirmDialog, Tabs } from '../components/ui'
import { PageLayout } from '../components/Layout'

const IMAGES = ['ubuntu:22.04', 'ubuntu:20.04', 'debian:11', 'alpine:3.18', 'centos:8']
const CPU_OPTIONS = [1, 2, 4, 8, 16]
const MEMORY_OPTIONS = [512, 1024, 2048, 4096, 8192, 16384, 32768]
const DISK_OPTIONS = [10, 20, 40, 80, 160, 320]

// State color mapping
const STATE_COLORS = {
  'REQUESTED': 'status-pending',
  'VALIDATING': 'status-pending',
  'SCHEDULING': 'status-pending',
  'PROVISIONING': 'status-pending',
  'BOOTSTRAPPING': 'status-pending',
  'CONFIGURING_NETWORK': 'status-pending',
  'HEALTHCHECKING': 'status-pending',
  'RUNNING': 'status-active',
  'STOPPING': 'status-pending',
  'STOPPED': 'status-error',
  'STARTING': 'status-pending',
  'REBOOTING': 'status-pending',
  'TERMINATING': 'status-error',
  'TERMINATED': 'status-error',
  'FAILED': 'status-error',
  'ROLLING_BACK': 'status-error',
}

export function InstancesPage() {
  const { data: instances, loading, refetch } = useApi(() => api.getInstances())
  const { data: hosts } = useApi(() => api.getHosts())
  const createModal = useToggle()
  const detailModal = useToggle()
  const deleteModal = useToggle()
  
  const [form, setForm] = useState({
    name: '',
    image: 'ubuntu:22.04',
    cpu: 2,
    memory_mb: 2048,
    disk_gb: 20,
    network_segment: 'default',
    startup_script: ''
  })
  const [selectedInstance, setSelectedInstance] = useState(null)
  const [creating, setCreating] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('instances')

  const updateForm = (key, value) => setForm({ ...form, [key]: value })

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await api.createInstance(api.defaultProjectId, form)
      setForm({ name: '', image: 'ubuntu:22.04', cpu: 2, memory_mb: 2048, disk_gb: 20, network_segment: 'default', startup_script: '' })
      createModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setCreating(false)
  }

  const handleAction = async (action) => {
    if (!selectedInstance) return
    setActionLoading(true)
    try {
      switch (action) {
        case 'stop':
          await api.stopInstance(selectedInstance.id)
          break
        case 'start':
          await api.startInstance(selectedInstance.id)
          break
        case 'reboot':
          await api.rebootInstance(selectedInstance.id)
          break
        case 'terminate':
          await api.terminateInstance(selectedInstance.id)
          deleteModal.setFalse()
          detailModal.setFalse()
          break
      }
      refetch()
      if (action !== 'terminate') {
        // Refresh instance details
        const updated = await api.getInstance(selectedInstance.id)
        setSelectedInstance(updated)
      }
    } catch (e) {
      alert('Error: ' + e.message)
    }
    setActionLoading(false)
  }

  const openDetail = (instance) => {
    setSelectedInstance(instance)
    detailModal.setTrue()
  }

  const openDelete = (instance) => {
    setSelectedInstance(instance)
    deleteModal.setTrue()
  }

  const instanceColumns = [
    { 
      header: 'Instance', 
      key: 'name',
      render: row => (
        <div className="resource-name" onClick={() => openDetail(row)} style={{ cursor: 'pointer' }}>
          <div className="resource-icon instance"><Server size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            <div className="text-muted">{row.id?.substring(0, 8)}</div>
          </div>
        </div>
      )
    },
    { 
      header: 'State', 
      key: 'state', 
      render: row => (
        <span className={`status ${STATE_COLORS[row.state] || 'status-pending'}`}>
          <span className="status-dot" />
          {row.state}
        </span>
      )
    },
    { header: 'Image', key: 'image', render: row => <span className="code">{row.image}</span> },
    { header: 'vCPU', key: 'cpu', render: row => `${row.cpu} vCPU` },
    { header: 'Memory', key: 'memory', render: row => `${row.memory_mb} MB` },
    { header: 'IP Address', key: 'ip', render: row => row.ip_address ? <span className="code">{row.ip_address}</span> : <span className="text-muted">-</span> },
    { 
      header: 'Actions', 
      key: 'actions',
      render: row => (
        <div className="action-buttons">
          <Button size="sm" variant="secondary" icon={Monitor} onClick={() => openDetail(row)}>Details</Button>
          {row.state === 'RUNNING' && (
            <>
              <Button size="sm" variant="secondary" icon={Square} onClick={() => { setSelectedInstance(row); handleAction('stop') }}>Stop</Button>
              <Button size="sm" variant="secondary" icon={RotateCcw} onClick={() => { setSelectedInstance(row); handleAction('reboot') }}>Reboot</Button>
            </>
          )}
          {row.state === 'STOPPED' && (
            <Button size="sm" variant="primary" icon={Play} onClick={() => { setSelectedInstance(row); handleAction('start') }}>Start</Button>
          )}
          <Button size="sm" variant="danger" icon={Power} onClick={() => openDelete(row)}>Terminate</Button>
        </div>
      )
    },
  ]

  const hostColumns = [
    { 
      header: 'Host', 
      key: 'name',
      render: row => (
        <div className="resource-name">
          <div className="resource-icon host"><Server size={14} /></div>
          <div>
            <span className="code">{row.name}</span>
            <div className="text-muted">{row.hostname}</div>
          </div>
        </div>
      )
    },
    { header: 'Zone', key: 'zone', render: row => <span className="code">{row.zone}</span> },
    { header: 'Status', key: 'status', render: row => <Status status={row.status} /> },
    { 
      header: 'CPU', 
      key: 'cpu', 
      render: row => (
        <div className="resource-usage">
          <span>{row.cpu_allocated}/{row.cpu_total} cores</span>
          <div className="usage-bar">
            <div className="usage-fill" style={{ width: `${(row.cpu_allocated / row.cpu_total) * 100}%` }} />
          </div>
        </div>
      )
    },
    { 
      header: 'Memory', 
      key: 'memory', 
      render: row => (
        <div className="resource-usage">
          <span>{Math.round(row.memory_allocated_mb / 1024)}/{Math.round(row.memory_total_mb / 1024)} GB</span>
          <div className="usage-bar">
            <div className="usage-fill" style={{ width: `${(row.memory_allocated_mb / row.memory_total_mb) * 100}%` }} />
          </div>
        </div>
      )
    },
    { header: 'Instances', key: 'instances', render: row => row.instance_count || 0 },
    { header: 'IP', key: 'ip', render: row => <span className="code">{row.ip_address}</span> },
  ]

  return (
    <PageLayout 
      title="Instances" 
      subtitle="Manage compute instances (EC2-like)"
      actions={
        <div className="button-group">
          <Button variant="secondary" icon={RefreshCw} onClick={refetch}>Refresh</Button>
          <Button variant="primary" icon={Plus} onClick={createModal.setTrue}>Launch Instance</Button>
        </div>
      }
    >
      {/* Tabs */}
      <div className="page-tabs">
        <button 
          className={`page-tab ${activeTab === 'instances' ? 'active' : ''}`}
          onClick={() => setActiveTab('instances')}
        >
          <Server size={16} /> Instances
        </button>
        <button 
          className={`page-tab ${activeTab === 'hosts' ? 'active' : ''}`}
          onClick={() => setActiveTab('hosts')}
        >
          <Cpu size={16} /> Compute Hosts
        </button>
      </div>

      {activeTab === 'instances' && (
        <Card>
          <Table columns={instanceColumns} data={instances} loading={loading} emptyMessage="No instances running. Launch your first instance!" />
        </Card>
      )}

      {activeTab === 'hosts' && (
        <Card>
          <Table columns={hostColumns} data={hosts} loading={loading} emptyMessage="No compute hosts available." />
        </Card>
      )}

      {/* Create Instance Modal */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Launch Instance"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Play} onClick={handleCreate} loading={creating}>Launch Instance</Button>
          </>
        }
      >
        <div className="instance-form">
          <div className="form-section">
            <h4 className="form-section-title"><Server size={16} /> Basic Configuration</h4>
            <Input label="Instance Name" value={form.name} onChange={e => updateForm('name', e.target.value)} placeholder="my-web-server" />
            <Select label="Image" value={form.image} onChange={e => updateForm('image', e.target.value)} options={IMAGES} />
          </div>

          <div className="form-section">
            <h4 className="form-section-title"><Cpu size={16} /> Compute Resources</h4>
            <div className="grid-3">
              <Select label="vCPU" value={form.cpu} onChange={e => updateForm('cpu', +e.target.value)} 
                options={CPU_OPTIONS.map(c => ({ value: c, label: `${c} vCPU` }))} />
              <Select label="Memory" value={form.memory_mb} onChange={e => updateForm('memory_mb', +e.target.value)} 
                options={MEMORY_OPTIONS.map(m => ({ value: m, label: `${m} MB (${m/1024} GB)` }))} />
              <Select label="Disk" value={form.disk_gb} onChange={e => updateForm('disk_gb', +e.target.value)} 
                options={DISK_OPTIONS.map(d => ({ value: d, label: `${d} GB` }))} />
            </div>
          </div>

          <div className="form-section">
            <h4 className="form-section-title"><Network size={16} /> Network</h4>
            <Input label="Network Segment" value={form.network_segment} onChange={e => updateForm('network_segment', e.target.value)} placeholder="default" />
          </div>

          <div className="form-section">
            <h4 className="form-section-title"><Activity size={16} /> Startup Script (cloud-init)</h4>
            <textarea 
              className="code-editor small"
              value={form.startup_script}
              onChange={e => updateForm('startup_script', e.target.value)}
              placeholder="#!/bin/bash&#10;apt-get update&#10;apt-get install -y nginx"
              spellCheck={false}
            />
          </div>
        </div>
      </Modal>

      {/* Instance Detail Modal */}
      <Modal 
        open={detailModal.value} 
        onClose={detailModal.setFalse} 
        title={
          <div className="modal-title-with-icon">
            <Server size={20} />
            <span>Instance: {selectedInstance?.name}</span>
          </div>
        }
        size="lg"
        footer={
          <div className="modal-footer-actions">
            <Button variant="secondary" onClick={detailModal.setFalse}>Close</Button>
            {selectedInstance?.state === 'RUNNING' && (
              <>
                <Button variant="secondary" icon={Square} onClick={() => handleAction('stop')} loading={actionLoading}>Stop</Button>
                <Button variant="secondary" icon={RotateCcw} onClick={() => handleAction('reboot')} loading={actionLoading}>Reboot</Button>
              </>
            )}
            {selectedInstance?.state === 'STOPPED' && (
              <Button variant="primary" icon={Play} onClick={() => handleAction('start')} loading={actionLoading}>Start</Button>
            )}
            <Button variant="danger" icon={Power} onClick={() => deleteModal.setTrue()}>Terminate</Button>
          </div>
        }
      >
        {selectedInstance && (
          <div className="instance-detail">
            <div className="detail-header">
              <span className={`status large ${STATE_COLORS[selectedInstance.state] || 'status-pending'}`}>
                <span className="status-dot" />
                {selectedInstance.state}
              </span>
            </div>

            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Instance ID</span>
                <span className="detail-value code">{selectedInstance.id}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Image</span>
                <span className="detail-value code">{selectedInstance.image}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">vCPU</span>
                <span className="detail-value">{selectedInstance.cpu} cores</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Memory</span>
                <span className="detail-value">{selectedInstance.memory_mb} MB</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Disk</span>
                <span className="detail-value">{selectedInstance.disk_gb} GB</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">IP Address</span>
                <span className="detail-value code">{selectedInstance.ip_address || '-'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">DNS Name</span>
                <span className="detail-value code">{selectedInstance.dns_name || '-'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Host</span>
                <span className="detail-value code">{selectedInstance.host_name || selectedInstance.host_id || '-'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Zone</span>
                <span className="detail-value">{selectedInstance.zone || 'default'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Network</span>
                <span className="detail-value">{selectedInstance.network_segment || 'default'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Created</span>
                <span className="detail-value">{new Date(selectedInstance.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Terminate Confirmation */}
      <ConfirmDialog
        open={deleteModal.value}
        onClose={deleteModal.setFalse}
        onConfirm={() => handleAction('terminate')}
        title="Terminate Instance"
        message={`Are you sure you want to terminate instance "${selectedInstance?.name}"? This action cannot be undone.`}
        confirmText="Terminate"
        loading={actionLoading}
      />
    </PageLayout>
  )
}

export default InstancesPage
