import { useState } from 'react'

export default function NewJob({ onCreated, apiBase }) {
  const [form, setForm] = useState({
    driver_phone: '',
    driver_name: '',
    vehicle_info: '',
    location: '',
    raw_message: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.raw_message.trim()) {
      setError('Problem description is required')
      return
    }
    setLoading(true)
    setError('')
    try {
      const r = await fetch(`${apiBase}/api/v1/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, source: 'manual' }),
      })
      if (!r.ok) throw new Error('Failed to create job')
      const data = await r.json()
      onCreated(data.id)
    } catch (e) {
      setError(e.message || 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">New Job</h1>
        <p className="text-sm text-slate-500 mt-1">Manually create a roadside assistance job — the AI agent will dispatch automatically</p>
      </div>

      <form onSubmit={submit} className="space-y-4">
        {/* Problem */}
        <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Problem Description *</h2>
          <textarea
            value={form.raw_message}
            onChange={e => set('raw_message', e.target.value)}
            placeholder="Describe the issue in plain language, e.g. 'Truck has a blown rear tire on I-95 mile marker 42, driver is safe on the shoulder'"
            rows={4}
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-none"
          />
        </div>

        {/* Driver info */}
        <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Driver & Vehicle</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500 block mb-1">Driver Name</label>
              <input
                type="text"
                value={form.driver_name}
                onChange={e => set('driver_name', e.target.value)}
                placeholder="John Smith"
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Driver Phone</label>
              <input
                type="tel"
                value={form.driver_phone}
                onChange={e => set('driver_phone', e.target.value)}
                placeholder="+1 555 000 0000"
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-slate-500 block mb-1">Vehicle Info</label>
              <input
                type="text"
                value={form.vehicle_info}
                onChange={e => set('vehicle_info', e.target.value)}
                placeholder="2022 Freightliner Cascadia — Unit #447"
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Location */}
        <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Location</h2>
          <input
            type="text"
            value={form.location}
            onChange={e => set('location', e.target.value)}
            placeholder="I-95 Northbound, Mile Marker 42, near Stamford CT"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-colors"
        >
          {loading ? '⚡ Dispatching AI Agent...' : 'Create Job & Dispatch Agent'}
        </button>
      </form>
    </div>
  )
}
