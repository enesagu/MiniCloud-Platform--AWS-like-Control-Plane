// API Service - connects to FastAPI backend via nginx proxy
const API_URL = import.meta.env.VITE_API_URL || ''

class ApiService {
  constructor() {
    this.baseUrl = API_URL
    this.defaultOrgId = 'org-default'
    this.defaultProjectId = 'proj-default'
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    }
    
    const res = await fetch(url, config)
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }

  get = (endpoint) => this.request(endpoint)
  post = (endpoint, data) => this.request(endpoint, { method: 'POST', body: JSON.stringify(data) })
  put = (endpoint, data) => this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) })
  delete = (endpoint) => this.request(endpoint, { method: 'DELETE' })

  // Health
  health = () => this.get('/health')

  // Organizations
  getOrgs = () => this.get('/api/v1/orgs')
  createOrg = (data) => this.post('/api/v1/orgs', data)

  // Projects
  getProjects = (orgId = this.defaultOrgId) => this.get(`/api/v1/orgs/${orgId}/projects`)
  createProject = (orgId, data) => this.post(`/api/v1/orgs/${orgId}/projects`, data)

  // Resources
  getResources = (projectId = this.defaultProjectId, type = null) => 
    this.get(`/api/v1/projects/${projectId}/resources${type ? `?type=${type}` : ''}`)
  createResource = (projectId, data) => this.post(`/api/v1/projects/${projectId}/resources`, data)
  deleteResource = (projectId, resourceId) => this.delete(`/api/v1/projects/${projectId}/resources/${resourceId}`)

  // Buckets
  getBuckets = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/buckets`)
  createBucket = (projectId, name) => this.post(`/api/v1/projects/${projectId}/buckets?name=${name}`, {})
  deleteBucket = (projectId, name) => this.delete(`/api/v1/projects/${projectId}/buckets/${name}`)

  // Functions
  getFunctions = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/functions`)
  createFunction = (projectId, data) => 
    this.post(`/api/v1/projects/${projectId}/functions?name=${data.name}&runtime=${data.runtime}&memory_mb=${data.memory}&timeout_seconds=${data.timeout}`, { code: data.code })
  deleteFunction = (projectId, functionId) => this.delete(`/api/v1/projects/${projectId}/functions/${functionId}`)
  invokeFunction = (functionId, payload = {}) => this.post(`/api/v1/functions/${functionId}/invoke`, payload)
  updateFunctionCode = (functionId, code) => this.put(`/api/v1/functions/${functionId}/code`, { code })
  getFunction = (projectId, functionId) => this.get(`/api/v1/projects/${projectId}/functions/${functionId}`)


  // Workflows
  getWorkflows = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/workflows`)
  createWorkflow = (projectId, data) => 
    this.post(`/api/v1/projects/${projectId}/workflows?name=${data.name}`, { definition: data.definition || {} })
  deleteWorkflow = (projectId, workflowId) => this.delete(`/api/v1/projects/${projectId}/workflows/${workflowId}`)
  startWorkflow = (name, input = {}) => this.post(`/api/v1/workflows/${name}/start`, input)
  getWorkflowRuns = (name) => this.get(`/api/v1/workflows/${name}/runs`)

  // Instances (EC2-like)
  getInstances = (projectId = this.defaultProjectId, state = null) => {
    let url = `/api/v1/projects/${projectId}/instances`
    if (state) url += `?state=${state}`
    return this.get(url)
  }
  getInstance = (instanceId) => this.get(`/api/v1/instances/${instanceId}`)
  createInstance = (projectId, data) => this.post(`/api/v1/projects/${projectId}/instances`, data)
  stopInstance = (instanceId) => this.post(`/api/v1/instances/${instanceId}/stop`, {})
  startInstance = (instanceId) => this.post(`/api/v1/instances/${instanceId}/start`, {})
  rebootInstance = (instanceId) => this.post(`/api/v1/instances/${instanceId}/reboot`, {})
  terminateInstance = (instanceId, force = false) => this.post(`/api/v1/instances/${instanceId}/terminate?force=${force}`, {})
  getInstanceEvents = (instanceId, limit = 50) => this.get(`/api/v1/instances/${instanceId}/events?limit=${limit}`)

  // Hosts (Compute Nodes)
  getHosts = (status = null, zone = null) => {
    let url = '/api/v1/hosts'
    const params = []
    if (status) params.push(`status=${status}`)
    if (zone) params.push(`zone=${zone}`)
    if (params.length) url += '?' + params.join('&')
    return this.get(url)
  }
  getHost = (hostId) => this.get(`/api/v1/hosts/${hostId}`)
  getHostInstances = (hostId) => this.get(`/api/v1/hosts/${hostId}/instances`)


  // Event Rules
  getEventRules = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/event-rules`)
  createEventRule = (projectId, data) => this.post(`/api/v1/projects/${projectId}/event-rules`, data)
  deleteEventRule = (projectId, ruleId) => this.delete(`/api/v1/projects/${projectId}/event-rules/${ruleId}`)

  // Users
  getUsers = (orgId = this.defaultOrgId) => this.get(`/api/v1/orgs/${orgId}/users`)
  createUser = (orgId, data) => this.post(`/api/v1/orgs/${orgId}/users`, data)
  deleteUser = (orgId, userId) => this.delete(`/api/v1/orgs/${orgId}/users/${userId}`)

  // Policies
  getPolicies = (orgId = this.defaultOrgId) => this.get(`/api/v1/orgs/${orgId}/policies`)
  createPolicy = (orgId, data) => this.post(`/api/v1/orgs/${orgId}/policies`, data)
  simulatePolicy = (action, resource, context = {}) => 
    this.post(`/api/v1/policies/simulate?action=${action}&resource=${resource}`, context)

  // Audit Logs
  getAuditLogs = (orgId = this.defaultOrgId, filters = {}) => {
    const params = new URLSearchParams(filters).toString()
    return this.get(`/api/v1/orgs/${orgId}/audit-logs${params ? `?${params}` : ''}`)
  }

  // Usage/Metrics
  getUsage = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/usage`)

  // Topics (SNS-like)
  getTopics = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/topics`)
  createTopic = (projectId, data) => this.post(`/api/v1/projects/${projectId}/topics`, data)
  deleteTopic = (projectId, topicId) => this.delete(`/api/v1/projects/${projectId}/topics/${topicId}`)
  publishToTopic = (topicId, message) => this.post(`/api/v1/topics/${topicId}/publish`, message)
  
  // Subscriptions
  getSubscriptions = (topicId) => this.get(`/api/v1/topics/${topicId}/subscriptions`)
  createSubscription = (topicId, data) => this.post(`/api/v1/topics/${topicId}/subscriptions`, data)
  deleteSubscription = (subscriptionId) => this.delete(`/api/v1/subscriptions/${subscriptionId}`)

  // Queues (SQS-like)
  getQueues = (projectId = this.defaultProjectId) => this.get(`/api/v1/projects/${projectId}/queues`)
  createQueue = (projectId, data) => this.post(`/api/v1/projects/${projectId}/queues`, data)
  getQueue = (queueId) => this.get(`/api/v1/queues/${queueId}`)
  deleteQueue = (projectId, queueId) => this.delete(`/api/v1/projects/${projectId}/queues/${queueId}`)
  purgeQueue = (queueId) => this.post(`/api/v1/queues/${queueId}/purge`, {})
  
  // Queue Messages
  sendMessage = (queueId, message) => this.post(`/api/v1/queues/${queueId}/messages`, message)
  receiveMessages = (queueId, maxMessages = 10) => this.get(`/api/v1/queues/${queueId}/messages?max_messages=${maxMessages}`)
  deleteMessage = (queueId, receiptHandle) => this.delete(`/api/v1/queues/${queueId}/messages/${receiptHandle}`)
}

export const api = new ApiService()
export default api
