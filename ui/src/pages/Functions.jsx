import React, { useState, useEffect } from 'react'
import { Code, Plus, Trash2, RefreshCw, Play, Edit3, Save, FileCode, Terminal } from 'lucide-react'
import { useApi, useToggle } from '../hooks'
import { api } from '../api'
import { Button, Card, Modal, Input, Select, Table, Status, ConfirmDialog, CodeBlock, Tabs } from '../components/ui'
import { PageLayout } from '../components/Layout'

const RUNTIMES = ['python3.10', 'python3.9', 'nodejs18.x', 'nodejs16.x', 'go1.x', 'java11']
const MEMORY_OPTIONS = [128, 256, 512, 1024, 2048]

// Default code templates for each runtime
const CODE_TEMPLATES = {
  'python3.10': `def handler(event, context):
    """
    Lambda-style function handler
    
    Args:
        event: Input event data (dict)
        context: Runtime context information
    
    Returns:
        Response object or value
    """
    print(f"Received event: {event}")
    
    # Your code here
    name = event.get('name', 'World')
    
    return {
        'statusCode': 200,
        'body': {
            'message': f'Hello, {name}!',
            'input': event
        }
    }
`,
  'python3.9': `def handler(event, context):
    """Lambda-style function handler"""
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': {'message': f'Hello, {name}!'}
    }
`,
  'nodejs18.x': `exports.handler = async (event, context) => {
    // Lambda-style function handler
    console.log('Received event:', JSON.stringify(event));
    
    const name = event.name || 'World';
    
    return {
        statusCode: 200,
        body: {
            message: \`Hello, \${name}!\`,
            input: event
        }
    };
};
`,
  'nodejs16.x': `exports.handler = async (event) => {
    const name = event.name || 'World';
    return {
        statusCode: 200,
        body: { message: \`Hello, \${name}!\` }
    };
};
`,
  'go1.x': `package main

import (
    "context"
    "fmt"
)

type Event struct {
    Name string \`json:"name"\`
}

type Response struct {
    StatusCode int    \`json:"statusCode"\`
    Message    string \`json:"message"\`
}

func Handler(ctx context.Context, event Event) (Response, error) {
    name := event.Name
    if name == "" {
        name = "World"
    }
    return Response{
        StatusCode: 200,
        Message:    fmt.Sprintf("Hello, %s!", name),
    }, nil
}
`,
  'java11': `package example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.Map;
import java.util.HashMap;

public class Handler implements RequestHandler<Map<String, Object>, Map<String, Object>> {
    
    @Override
    public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
        String name = (String) event.getOrDefault("name", "World");
        
        Map<String, Object> response = new HashMap<>();
        response.put("statusCode", 200);
        response.put("message", "Hello, " + name + "!");
        
        return response;
    }
}
`
}

export function FunctionsPage() {
  const { data: functions, loading, refetch } = useApi(() => api.getFunctions())
  const createModal = useToggle()
  const invokeModal = useToggle()
  const deleteModal = useToggle()
  const editModal = useToggle()
  
  const [form, setForm] = useState({ 
    name: '', 
    runtime: 'python3.10', 
    memory: 128, 
    timeout: 30, 
    handler: 'main.handler',
    code: CODE_TEMPLATES['python3.10']
  })
  const [selectedFn, setSelectedFn] = useState(null)
  const [invokePayload, setInvokePayload] = useState('{}')
  const [invokeResult, setInvokeResult] = useState(null)
  const [creating, setCreating] = useState(false)
  const [invoking, setInvoking] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editCode, setEditCode] = useState('')
  const [activeTab, setActiveTab] = useState('code')

  // Update code template when runtime changes
  useEffect(() => {
    if (!form.code || form.code === CODE_TEMPLATES[form.prevRuntime]) {
      setForm(f => ({ ...f, code: CODE_TEMPLATES[f.runtime], prevRuntime: f.runtime }))
    }
  }, [form.runtime])

  const updateForm = (key, value) => {
    if (key === 'runtime') {
      setForm({ ...form, [key]: value, prevRuntime: form.runtime })
    } else {
      setForm({ ...form, [key]: value })
    }
  }

  const handleCreate = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      const result = await api.createFunction(api.defaultProjectId, form)
      // Save the code after creating
      if (result?.id) {
        await api.updateFunctionCode(result.id, form.code)
      }
      setForm({ name: '', runtime: 'python3.10', memory: 128, timeout: 30, handler: 'main.handler', code: CODE_TEMPLATES['python3.10'] })
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

  const handleSaveCode = async () => {
    if (!selectedFn) return
    setSaving(true)
    try {
      await api.updateFunctionCode(selectedFn.id, editCode)
      // Update local state
      selectedFn.spec = { ...selectedFn.spec, code: editCode }
      editModal.setFalse()
      refetch()
    } catch (e) {
      alert('Error saving code: ' + e.message)
    }
    setSaving(false)
  }

  const openInvoke = (fn) => {
    setSelectedFn(fn)
    setInvokePayload('{\n  "name": "Test"\n}')
    setInvokeResult(null)
    invokeModal.setTrue()
  }

  const openEdit = (fn) => {
    setSelectedFn(fn)
    const runtime = fn.spec?.runtime || 'python3.10'
    setEditCode(fn.spec?.code || CODE_TEMPLATES[runtime])
    setActiveTab('code')
    editModal.setTrue()
  }

  const openDelete = (fn) => {
    setSelectedFn(fn)
    deleteModal.setTrue()
  }

  const getLanguage = (runtime) => {
    if (runtime?.startsWith('python')) return 'python'
    if (runtime?.startsWith('nodejs')) return 'javascript'
    if (runtime?.startsWith('go')) return 'go'
    if (runtime?.startsWith('java')) return 'java'
    return 'text'
  }

  const columns = [
    { 
      header: 'Name', 
      key: 'name',
      render: row => (
        <div className="resource-name" onClick={() => openEdit(row)} style={{ cursor: 'pointer' }}>
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
          <Button size="sm" variant="secondary" icon={Edit3} onClick={() => openEdit(row)}>Edit</Button>
          <Button size="sm" variant="primary" icon={Play} onClick={() => openInvoke(row)}>Test</Button>
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

      {/* Create Modal with Code Editor */}
      <Modal 
        open={createModal.value} 
        onClose={createModal.setFalse} 
        title="Create Function"
        size="xl"
        footer={
          <>
            <Button variant="secondary" onClick={createModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Plus} onClick={handleCreate} loading={creating}>Create Function</Button>
          </>
        }
      >
        <div className="function-create-form">
          <div className="form-section">
            <h4 className="form-section-title">Configuration</h4>
            <div className="grid-2">
              <Input label="Function Name" value={form.name} onChange={e => updateForm('name', e.target.value)} placeholder="my-function" />
              <Select label="Runtime" value={form.runtime} onChange={e => updateForm('runtime', e.target.value)} options={RUNTIMES} />
            </div>
            <div className="grid-3">
              <Select label="Memory" value={form.memory} onChange={e => updateForm('memory', +e.target.value)} 
                options={MEMORY_OPTIONS.map(m => ({ value: m, label: `${m} MB` }))} />
              <Input label="Timeout (sec)" type="number" value={form.timeout} onChange={e => updateForm('timeout', +e.target.value)} />
              <Input label="Handler" value={form.handler} onChange={e => updateForm('handler', e.target.value)} placeholder="main.handler" />
            </div>
          </div>
          
          <div className="form-section">
            <h4 className="form-section-title">
              <FileCode size={16} /> Function Code
            </h4>
            <div className="code-editor-container">
              <div className="code-editor-header">
                <span className="code-file-name">
                  {form.runtime?.startsWith('python') ? 'main.py' : 
                   form.runtime?.startsWith('nodejs') ? 'index.js' :
                   form.runtime?.startsWith('go') ? 'main.go' : 'Handler.java'}
                </span>
                <span className="code-runtime-badge">{form.runtime}</span>
              </div>
              <textarea 
                className="code-editor"
                value={form.code}
                onChange={e => updateForm('code', e.target.value)}
                spellCheck={false}
              />
            </div>
          </div>
        </div>
      </Modal>

      {/* Edit Code Modal */}
      <Modal 
        open={editModal.value} 
        onClose={editModal.setFalse} 
        title={
          <div className="modal-title-with-icon">
            <FileCode size={20} />
            <span>Edit Function: {selectedFn?.name}</span>
          </div>
        }
        size="xl"
        footer={
          <>
            <Button variant="secondary" onClick={editModal.setFalse}>Cancel</Button>
            <Button variant="primary" icon={Save} onClick={handleSaveCode} loading={saving}>Save & Deploy</Button>
          </>
        }
      >
        <div className="function-editor">
          <div className="editor-tabs">
            <button 
              className={`editor-tab ${activeTab === 'code' ? 'active' : ''}`}
              onClick={() => setActiveTab('code')}
            >
              <FileCode size={14} /> Code
            </button>
            <button 
              className={`editor-tab ${activeTab === 'test' ? 'active' : ''}`}
              onClick={() => setActiveTab('test')}
            >
              <Terminal size={14} /> Test
            </button>
            <button 
              className={`editor-tab ${activeTab === 'config' ? 'active' : ''}`}
              onClick={() => setActiveTab('config')}
            >
              <Code size={14} /> Configuration
            </button>
          </div>

          {activeTab === 'code' && (
            <div className="code-editor-container large">
              <div className="code-editor-header">
                <span className="code-file-name">
                  {selectedFn?.spec?.runtime?.startsWith('python') ? 'main.py' : 
                   selectedFn?.spec?.runtime?.startsWith('nodejs') ? 'index.js' :
                   selectedFn?.spec?.runtime?.startsWith('go') ? 'main.go' : 'Handler.java'}
                </span>
                <span className="code-runtime-badge">{selectedFn?.spec?.runtime}</span>
              </div>
              <textarea 
                className="code-editor"
                value={editCode}
                onChange={e => setEditCode(e.target.value)}
                spellCheck={false}
                placeholder="Write your function code here..."
              />
            </div>
          )}

          {activeTab === 'test' && (
            <div className="test-panel">
              <div className="test-input">
                <label className="form-label">Test Event (JSON)</label>
                <textarea 
                  className="code-editor small"
                  value={invokePayload}
                  onChange={e => setInvokePayload(e.target.value)}
                  spellCheck={false}
                  placeholder='{"key": "value"}'
                />
                <Button 
                  variant="primary" 
                  icon={Play} 
                  onClick={handleInvoke} 
                  loading={invoking}
                  style={{ marginTop: '1rem' }}
                >
                  Run Test
                </Button>
              </div>
              {invokeResult && (
                <div className="test-output">
                  <label className="form-label">Execution Result</label>
                  <CodeBlock code={invokeResult} />
                </div>
              )}
            </div>
          )}

          {activeTab === 'config' && (
            <div className="config-panel">
              <div className="config-item">
                <span className="config-label">Function Name</span>
                <span className="config-value code">{selectedFn?.name}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Runtime</span>
                <span className="config-value code">{selectedFn?.spec?.runtime}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Handler</span>
                <span className="config-value code">{selectedFn?.spec?.handler}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Memory</span>
                <span className="config-value">{selectedFn?.spec?.memory_mb} MB</span>
              </div>
              <div className="config-item">
                <span className="config-label">Timeout</span>
                <span className="config-value">{selectedFn?.spec?.timeout_seconds} seconds</span>
              </div>
              <div className="config-item">
                <span className="config-label">Status</span>
                <Status status={selectedFn?.state?.status || 'Active'} />
              </div>
              <div className="config-item">
                <span className="config-label">Total Invocations</span>
                <span className="config-value">{selectedFn?.state?.invocation_count || 0}</span>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Invoke/Test Modal */}
      <Modal 
        open={invokeModal.value} 
        onClose={invokeModal.setFalse} 
        title={`Test Function: ${selectedFn?.name}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={invokeModal.setFalse}>Close</Button>
            <Button variant="primary" icon={Play} onClick={handleInvoke} loading={invoking}>Run Test</Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Test Event (JSON)</label>
          <textarea 
            className="code-editor small" 
            value={invokePayload} 
            onChange={e => setInvokePayload(e.target.value)}
            spellCheck={false}
          />
        </div>
        {invokeResult && (
          <div className="form-group">
            <label className="form-label">
              {invokeResult.error ? '❌ Error' : '✅ Execution Result'}
            </label>
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
        message={`Are you sure you want to delete function "${selectedFn?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        loading={deleting}
      />
    </PageLayout>
  )
}

export default FunctionsPage
