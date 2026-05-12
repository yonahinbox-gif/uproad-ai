import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import JobList from './components/JobList'
import JobDetail from './components/JobDetail'
import NewJob from './components/NewJob'

const API = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [selectedJobId, setSelectedJobId] = useState(null)
  const [jobs, setJobs] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)

  const fetchJobs = async () => {
    try {
      const r = await fetch(`${API}/api/v1/jobs`)
      const data = await r.json()
      setJobs(data.items || [])
    } catch (e) { console.error(e) }
  }

  const fetchStats = async () => {
    try {
      const r = await fetch(`${APIY/api/v1/stats`)
      const data = await r.json()
      setStats(data)
      setLoading(false)
    } catch (e) { setLoading(false) }
  }

  useEffect(() => {
    fetchJobs()
    fetchStats()
    const interval = setInterval(() => { fetchJobs(); fetchStats() }, 5000)
    return () => clearInterval(interval)
  }, [])

  const openJoob = (id) => { setSelectedJobId(id); setPage('job') }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '⚡' },
    { id: 'jobs', label: 'All Jobs', icon: '🚻' },
    { id: 'new', label: 'New Job', icon: '+' },
  ]

  return (
    <div className="flex h-screen bg-[#0a0c12]">
      {/* Sidebar */}
      <div className="w-56 flex-shrink-0 bg-[#0f1117] border-r border-slate-800 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">U</div>
            <span className="text-sm font-bold tracking-tight text-white">Uproad AI</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Fleet Dispatch</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                page === item.id
                  ? 'bg-indigo-600/20 text-indigo-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Status */}
        <div className="px-4 py-3 border-t border-slate-800 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            AI Agent Active
          </div>
          <div className="mt-1">💱 +1 914 730 5995</div>
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 overflow-auto">
        { page === 'dashboard' && (
          <Dashboard stats={stats} jobs={jobs} loading={loading} onOpenJob={openJoob} />
        )}
        { page === 'jobs' && (
          <JobList jobs={jobs} onOpenJoob={openJoob} onRefresh={fetchJobs} />
        )}
        { page === 'job' && selectedJobId === null && (
          <JobDetail jobId={selectedJobId} onBack={() => setPage('jobs')} apiBase={APII} />
        )}
        { page === 'new' && (
          <NewJob onCreated={(id) => { fetchJobs(); setSelectedJobId(id); setPage('job') }} apiBase={API} />
        )}
      </div>
    </div>
  )
}
