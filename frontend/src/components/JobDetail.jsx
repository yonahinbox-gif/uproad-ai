import { useState, useEffect } from 'react'
import { formatDistanceToNow } from '../utils'

const STATUS_COLORS = {
  OPEN: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  IN_PROGRESS: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  NEEDS_APPROVAL: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  RESOLVED: 'bg-green-500/20 text-green-300 border-green-500/30',
}

const STATUS_OPTIONS = ['OPEN', 'IN_PROGRESS', 'NEEDS_APPROVAL', 'RESOLVED']

export default function JobDetail({ jobId, onBack, apiBase }) {
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  const fetchJob = async () => {
    try {
      const r = await fetch(`${apiBase}/api/v1/jobs/${jobId}`)
      const data = await r.json()
      setJob(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJob()
    const interval = setInterval(fetchJob, 5000)
    return () => clearInterval(interval)
  }, [jobId])

  const updateStatus = async (status) => {
    setUpdating(true)
    try {
      await fetch(`${apiBase}/api/v1/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
      await fetchJob()
    } catch (e) {
      console.error(e)
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-slate-500 text-sm">Loading...</div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="p-6">
        <button onClick={onBack} className="text-slate-400 hover:text-white text-sm mb-4">← Back</button>
        <div className="text-slate-500">Job not found</div>
      </div>
    )
  }

  const actions = job.actions || []
  const agentRuns = job.agent_runs || []

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="text-slate-400 hover:text-white text-sm transition-colors"
        >
          ← Back
        </button>
        <span className="text-slate-700">/</span>
        <span className="text-slate-400 text-sm">Job #{job.id}</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">{job.vehicle_info || 'Unknown Vehicle'}</h1>
          <p className="text-sm text-slate-400 mt-1">{job.summary || 'No summary'}</p>
          <div className="flex items-center gap-3 mt-2">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[job.status]}`}>
              {job.status.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-slate-500">
              {job.source === 'call' ? '📞 Call' : job.source === 'sms' ? '💬 SMS' : '🖥 Manual'}
            </span>
            {job.created_at && (
              <span className="text-xs text-slate-500">{formatDistanceToNow(job.created_at)}</span>
            )}
          </div>
        </div>

        {/* Status update */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Update status:</span>
          <select
            value={job.status}
            onChange={(e) => updateStatus(e.target.value)}
            disabled={updating}
            className="text-xs bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            {STATUS_OPTIONS.map(s => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Job info */}
        <div className="col-span-2 space-y-4">

          {/* Incident details */}
          <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Incident Details</h2>
            <div className="space-y-2 text-sm">
              {job.driver_name && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Driver</span>
                  <span className="text-slate-200">{job.driver_name}</span>
                </div>
              )}
              {job.driver_phone && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Phone</span>
                  <span className="text-slate-200">{job.driver_phone}</span>
                </div>
              )}
              {job.location && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Location</span>
                  <span className="text-slate-200 text-right max-w-xs">{job.location}</span>
                </div>
              )}
              {job.type && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Type</span>
                  <span className="text-slate-200">{job.type}</span>
                </div>
              )}
              {job.raw_message && (
                <div className="pt-2 border-t border-slate-800">
                  <p className="text-slate-500 text-xs mb-1">Raw message</p>
                  <p className="text-slate-300 text-xs leading-relaxed">{job.raw_message}</p>
                </div>
              )}
            </div>
          </div>

          {/* Vendor info */}
          {job.assigned_vendor_name && (
            <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Assigned Vendor</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Vendor</span>
                  <span className="text-indigo-400 font-medium">{job.assigned_vendor_name}</span>
                </div>
                {job.assigned_vendor_phone && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Phone</span>
                    <span className="text-slate-200">{job.assigned_vendor_phone}</span>
                  </div>
                )}
                {job.vendor_eta_minutes && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">ETA</span>
                    <span className="text-green-400">~{job.vendor_eta_minutes} min</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Agent actions */}
          {actions.length > 0 && (
            <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Agent Actions</h2>
              <div className="space-y-2">
                {actions.map((action, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span className="text-lg leading-none mt-0.5">
                      {action.type === 'sms_sent' ? '💬' :
                       action.type === 'call_made' ? '📞' :
                       action.type === 'vendor_found' ? '🔍' :
                       action.type === 'status_update' ? '🔄' : '⚡'}
                    </span>
                    <div className="min-w-0">
                      <p className="text-slate-200">{action.description || action.type}</p>
                      {action.to && <p className="text-xs text-slate-500 mt-0.5">→ {action.to}</p>}
                      {action.message && (
                        <p className="text-xs text-slate-400 mt-1 bg-slate-800/50 rounded px-2 py-1 italic">
                          "{action.message}"
                        </p>
                      )}
                      {action.timestamp && (
                        <p className="text-xs text-slate-600 mt-0.5">{formatDistanceToNow(action.timestamp)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar — agent run log */}
        <div className="space-y-4">
          <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">AI Agent Log</h2>
            {agentRuns.length === 0 ? (
              <p className="text-xs text-slate-600">No agent runs yet</p>
            ) : (
              <div className="space-y-3">
                {agentRuns.map((run, i) => (
                  <div key={i} className="text-xs border-l-2 border-indigo-600/40 pl-2">
                    <p className="text-indigo-300 font-medium mb-1">Run #{i + 1}</p>
                    {run.thinking && (
                      <p className="text-slate-500 leading-relaxed mb-1 italic">{run.thinking}</p>
                    )}
                    {run.message && (
                      <p className="text-slate-400 leading-relaxed">{run.message}</p>
                    )}
                    {run.tool_calls && run.tool_calls.map((tc, j) => (
                      <div key={j} className="mt-1 text-slate-500">
                        <span className="text-indigo-400/70">→ {tc.name}</span>
                        {tc.result && <span className="text-green-400/70"> ✓</span>}
                      </div>
                    ))}
                    {run.timestamp && (
                      <p className="text-slate-700 mt-1">{formatDistanceToNow(run.timestamp)}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
