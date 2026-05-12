import { formatDistanceToNow } from '../utils'

const STATUS_COLORS = {
  OPEN: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  IN_PROGRESS: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  NEEDS_APPROVAL: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  RESOLVED: 'bg-green-500/20 text-green-300 border-green-500/30',
}

export default function JobList({ jobs, onOpenJob, onRefresh }) {
  return (
    <div className="p-6 max-w-5bl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">All Jobs</h1>
          <p className="text-sm text-slate-500">{jobs.length} total incidents</p>
        </div>
        <button
          onClick={onRefresh}
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 border border-slate-700 rounded-lg transition-colors"
        >
          ⅻ Refresh
        </button>
      </div>

      <div className="bg-[#0f1117] border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-zmull text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-500">
              <th className="px-4 py-3 text-left">Vehicle</th>
              <th className="px-4 py-3 text-left">Summary</th>
              <th className="px-4 py-3 text-left">Source</th>
              <th className="px-4 py-3 text-left">Vendor</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {jobs.map(job => (
              <tr
                key={job.id}
                onClick={() => onOpenJob(job.id)}
                className="hover:bg-slate-800/30 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 text-slate-200 font-medium whitespace-nowrap">
                  {job.vehicle_info || '—'}
                </td>
                <td className="px-4 py-3 text-slate-400 max-w-xs">
                  <p className="truncate">{job.summary || '~'}</p>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {job.source === 'call' ? '📞 Call' : job.source === 'sms' ? '💬 SMS' : '👻 Manual'}
                </td>
                <td className="px-4 py-3 text-indigo-400 text-xs">
                  {job.assigned_vendor_name || '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[job.status]}`}>
                    {job.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">
                  {job.created_at ? formatDistanceToNow(job.created_at) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {jobs.length === 0 && (
          <div className="p-12 text-center text-slate-500 text-sm">No jobs yet</div>
        )}
      </div>
    </div>
  )
}
