import { formatDistanceToNow } from '../utils'

const STATUS_COLORS = {
  OPEN: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  IN_PROGRESS: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  NEEDS_APPROVAL: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  RESOLVED: 'bg-green-500/20 text-green-300 border-green-500/30',
}

export default function Dashboard({ stats, jobs, loading, onOpenJob }) {
  const byStatus = stats.by_status || {}
  const active = jobs.filter(j => ['OPEN','IN_PROGRESS','NEEDS_APPROVAL'].includes(j.status))

  const statCards = [
    { label: 'Open', value: byStatus.OPEN || 0, color: 'text-yellow-400' },
    { label: 'In Progress', value: byStatus.IN_PROGRESS || 0, color: 'text-blue-400' },
    { label: 'Needs Approval', value: byStatus.NEEDS_APPROVAL || 0, color: 'text-orange-400' },
    { label: 'Resolved', value: byStatus.RESOLVED || 0, color: 'text-green-400' },
  ]

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-slate-500">Fleet service activity overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {statCards.map(s => (
          <div key={s.label} className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">{s.label}</p>
            <p className={`text-3xl font-bold ${s.color}`}>{loading ? '—' : s.value}</p>
          </div>
        ))}
      </div>

      {/* Active jobs */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-300">
            Active Jobs
            <span className="ml-2 text-xs text-slate-500">{active.length} requiring attention</span>
          </h2>
        </div>
        <div className="space-y-2">
          {active.length === 0 && (
            <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-sm">
              No active jobs — all clear 🟢
            </div>
          )}
          {active.slice(0, 5).map(job => (
            <button
              key={job.id}
              onClick={() => onOpenJob(job.id)}
              className="w-full text-left bg-[#0f1117] border border-slate-800 hover:border-slate-600 rounded-xl p-4 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-white">
                      {job.vehicle_info || 'Unknown Vehicle'}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[job.status]}`}>
                      {job.status.replace('_', ' ')}
                    </span>
                    {job.source === 'call' && <span className="text-xs text-slate-500">📞 via call</span>}
                    {job.source === 'sms' && <span className="text-xs text-slate-500">💬 via SMS</span>}
                  </div>
                  <p className="text-sm text-slate-400 truncate">{job.summary}</p>
                  {job.assigned_vendor_name && (
                    <p className="text-xs text-indigo-400 mt-1">→ {job.assigned_vendor_name}{job.vendor_eta_minutes ? ` · ETA ~${job.vendor_eta_minutes}min` : ''}</p>
                  )}
                </div>
                <span className="text-xs text-slate-600 whitespace-nowrap">
                  {job.created_at ? formatDistanceToNow(job.created_at) : ''}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Recent Activity</h2>
        <div className="bg-[#0f1117] border border-slate-800 rounded-xl divide-y divide-slate-800">
          {jobs.slice(0, 8).map(job => (
            <button
              key={job.id}
              onClick={() => onOpenJob(job.id)}
              className="w-full text-left px-4 py-3 hover:bg-slate-800/40 transition-colors flex items-start justify-between gap-4"
            >
              <div className="min-w-0">
                <p className="text-sm text-slate-200 font-medium">{job.vehicle_info || 'Vehicle'}</p>
                <p className="text-xs text-slate-500 truncate">{job.summary}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[job.status]}`}>
                  {job.status.replace('_', ' ')}
                </span>
                <p className="text-xs text-slate-600 mt-1">{job.created_at ? formatDistanceToNow(job.created_at) : ''}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
