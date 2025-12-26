import React, { useState } from 'react'
import { BarChart3, Code, Folder, GitBranch, Zap, Shield, Terminal, Bell, Inbox } from 'lucide-react'
import { Sidebar, Header } from './components/Layout'
import { DashboardPage, BucketsPage, FunctionsPage, WorkflowsPage, EventRulesPage, TopicsPage, QueuesPage, IAMPage, AuditLogsPage } from './pages'

// Navigation configuration
const NAV_ITEMS = [
  { 
    section: 'Overview', 
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    ]
  },
  { 
    section: 'Compute', 
    items: [
      { id: 'functions', label: 'Functions', icon: Code },
      { id: 'workflows', label: 'Workflows', icon: GitBranch },
    ]
  },
  { 
    section: 'Storage', 
    items: [
      { id: 'buckets', label: 'Buckets', icon: Folder },
    ]
  },
  { 
    section: 'Messaging', 
    items: [
      { id: 'topics', label: 'Topics (SNS)', icon: Bell },
      { id: 'queues', label: 'Queues (SQS)', icon: Inbox },
    ]
  },
  { 
    section: 'Integration', 
    items: [
      { id: 'events', label: 'Event Rules', icon: Zap },
    ]
  },
  { 
    section: 'Security', 
    items: [
      { id: 'iam', label: 'IAM', icon: Shield },
    ]
  },
  { 
    section: 'Observability', 
    items: [
      { id: 'logs', label: 'Audit Logs', icon: Terminal },
    ]
  },
]

// Page titles
const PAGE_TITLES = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview of your MiniCloud resources' },
  functions: { title: 'Functions', subtitle: 'Serverless compute' },
  workflows: { title: 'Workflows', subtitle: 'Durable workflow orchestration' },
  buckets: { title: 'Buckets', subtitle: 'Object storage' },
  topics: { title: 'Topics (SNS)', subtitle: 'Pub/Sub messaging' },
  queues: { title: 'Queues (SQS)', subtitle: 'Message queues' },
  events: { title: 'Event Rules', subtitle: 'Event routing' },
  iam: { title: 'IAM', subtitle: 'Identity & Access Management' },
  logs: { title: 'Audit Logs', subtitle: 'Activity trail' },
}

// Page components mapping
const PAGES = {
  dashboard: DashboardPage,
  buckets: BucketsPage,
  functions: FunctionsPage,
  workflows: WorkflowsPage,
  topics: TopicsPage,
  queues: QueuesPage,
  events: EventRulesPage,
  iam: IAMPage,
  logs: AuditLogsPage,
}

function App() {
  const [activePage, setActivePage] = useState('dashboard')
  
  const PageComponent = PAGES[activePage] || DashboardPage
  const pageInfo = PAGE_TITLES[activePage] || PAGE_TITLES.dashboard

  return (
    <div className="app">
      <Sidebar 
        navItems={NAV_ITEMS} 
        activePage={activePage} 
        setActivePage={setActivePage} 
      />
      <main className="main">
        <Header title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <div className="content">
          <PageComponent />
        </div>
      </main>
    </div>
  )
}

export default App
