import React from 'react'

function StepCard({ step, index }) {
  const isError = Boolean(step?.stderr)
  const statusTone = isError
    ? 'border-rose-300/50 bg-rose-50 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100'
    : 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200'

  return (
    <div className={`animate-in-up rounded-xl border p-3 shadow-sm ${statusTone}`} style={{ animationDelay: `${index * 60}ms` }}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold uppercase tracking-wide">Step {step.step_id ?? index + 1}</span>
        <span className="opacity-80">{step.step_kind || 'action'}</span>
      </div>
      <code className="mt-2 block whitespace-pre-wrap break-words rounded-lg bg-white p-2 text-[11px] dark:bg-slate-900">{step.command}</code>
      {step.stdout ? <pre className="mt-2 whitespace-pre-wrap text-xs opacity-90">{step.stdout}</pre> : null}
      {step.stderr ? <pre className="mt-2 whitespace-pre-wrap text-xs text-rose-600 dark:text-rose-200">{step.stderr}</pre> : null}
    </div>
  )
}

function Card({ title, children, accent = 'emerald' }) {
  const accentClass = accent === 'rose'
    ? 'border-rose-500/20'
    : accent === 'amber'
      ? 'border-amber-500/20'
      : 'border-emerald-500/20'

  return (
    <div className={`rounded-2xl border ${accentClass} bg-white p-4 shadow-sm dark:bg-slate-900`}>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{title}</h3>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function AIPanel({ latestOutput, latestError, loading, onCopy }) {
  const plan = latestOutput?.plan || []
  const execution = latestOutput?.execution_result
  const executionSteps = Array.isArray(execution?.results) ? execution.results : []
  const intent = latestOutput?.intent || 'unknown'
  const safety = latestOutput?.safety || 'safe'

  return (
  <section className="flex h-full flex-col gap-3 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between px-1 pt-1">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">AI Reasoning</h2>
        {loading ? <span className="text-xs text-sky-500">Running...</span> : <span className="text-xs text-slate-500 dark:text-slate-400">Idle</span>}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        <Card title="Intent">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-900/90 px-2 py-1 text-xs text-slate-100 dark:bg-slate-100 dark:text-slate-900">{intent}</span>
            <span className={`rounded-full px-2 py-1 text-xs ${safety === 'danger' ? 'bg-rose-500/20 text-rose-600 dark:text-rose-300' : safety === 'caution' ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300' : 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300'}`}>
              {safety}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{latestOutput?.explanation || 'Waiting for command execution context...'}</p>
        </Card>

        <Card title="Execution Plan" accent="amber">
          {plan.length ? (
            <div className="space-y-2">
              {plan.map((step) => (
                <div key={`${step.id}-${step.command}`} className="animate-in-up rounded-xl border border-amber-500/25 bg-amber-500/10 p-2 text-xs text-amber-800 dark:text-amber-200">
                  <div className="font-medium">Step {step.id}: {step.description}</div>
                  <code className="mt-1 block whitespace-pre-wrap break-words text-[11px] opacity-85">{step.command}</code>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">No plan yet.</p>
          )}
        </Card>

        <Card title="Execution Logs">
          {executionSteps.length ? (
            <div className="space-y-2">
              {executionSteps.map((step, index) => (
                <StepCard key={`${step.step_id}-${index}`} step={step} index={index} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">Logs will appear after command execution.</p>
          )}

          {latestOutput ? (
            <button
              type="button"
              onClick={() => onCopy(JSON.stringify(latestOutput, null, 2))}
              className="mt-3 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs text-white transition hover:bg-slate-700 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-white"
            >
              Copy JSON
            </button>
          ) : null}
        </Card>

        {latestError ? (
          <Card title="Latest Error" accent="rose">
            <p className="whitespace-pre-wrap text-sm text-rose-700 dark:text-rose-300">{latestError.content}</p>
          </Card>
        ) : null}
      </div>
    </section>
  )
}

export default AIPanel
