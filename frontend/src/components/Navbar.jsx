import React from 'react'

const STATUS_STYLES = {
  connected: 'bg-emerald-400',
  running: 'bg-sky-400 animate-pulse',
  idle: 'bg-amber-300',
  disconnected: 'bg-rose-400',
  connecting: 'bg-zinc-400 animate-pulse',
}

function Navbar({ cwd, status, theme, onToggleTheme }) {
  const statusLabel = (status || 'idle').toUpperCase()
  const dotStyle = STATUS_STYLES[status] || STATUS_STYLES.idle

  return (
  <header className="relative z-10 mb-4 rounded-2xl border border-slate-200/70 bg-white px-5 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">NeuroShell</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">AI-assisted terminal</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <span className={`h-2.5 w-2.5 rounded-full ${dotStyle}`} />
            <span>{statusLabel}</span>
          </div>

          <div className="max-w-[28rem] truncate rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {cwd || '~'}
          </div>

          <button
            type="button"
            onClick={onToggleTheme}
            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </div>
    </header>
  )
}

export default Navbar
