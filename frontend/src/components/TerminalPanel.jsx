import React from 'react'

function TypewriterText({ text }) {
  return <span>{text}</span>
}

function getExecutionOutput(executionResult) {
  if (!executionResult) return { stdout: '', stderr: '' }

  if (typeof executionResult.stdout === 'string' || typeof executionResult.stderr === 'string') {
    return {
      stdout: executionResult.stdout || '',
      stderr: executionResult.stderr || '',
    }
  }

  if (Array.isArray(executionResult.results)) {
    const stdout = executionResult.results.map((step) => step?.stdout || '').filter(Boolean).join('\n')
    const stderr = executionResult.results.map((step) => step?.stderr || '').filter(Boolean).join('\n')
    return { stdout, stderr }
  }

  return { stdout: '', stderr: '' }
}

function CommandBubble({ entry, onCopyOutput }) {
  if (entry.type === 'input') {
    return (
      <div className="flex justify-end">
        <div className="group max-w-[82%] rounded-2xl rounded-tr-sm border border-emerald-300/60 bg-emerald-50 px-4 py-3 text-sm text-emerald-950 dark:border-emerald-500/30 dark:bg-emerald-500/15 dark:text-emerald-100">
          <div className="text-[11px] uppercase tracking-wide text-emerald-700/80 dark:text-emerald-200/80">Command</div>
          <div className="mt-1 break-words font-medium">{entry.content}</div>
        </div>
      </div>
    )
  }

  if (entry.type === 'error') {
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-rose-300/50 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
          <div className="text-[11px] uppercase tracking-wide text-rose-600 dark:text-rose-300">Error</div>
          <p className="mt-1 break-words">{entry.content}</p>
        </div>
      </div>
    )
  }

  const output = getExecutionOutput(entry.content.execution_result)
  const hasOutput = output.stdout || output.stderr

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-[90%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-slate-500 dark:text-slate-400">AI Execution</div>
            <p className="mt-1 text-slate-700 dark:text-slate-100">
              <TypewriterText text={entry.content.explanation || 'Execution completed'} />
            </p>
          </div>

          {hasOutput ? (
            <button
              onClick={() => onCopyOutput(`${output.stdout || ''}${output.stderr ? `\n${output.stderr}` : ''}`)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              type="button"
            >
              Copy
            </button>
          ) : null}
        </div>

        <div className="mt-2 rounded-xl bg-slate-100 p-3 dark:bg-slate-800">
          <code className="break-words text-xs text-emerald-700 dark:text-emerald-300">{entry.content.command}</code>
        </div>

        {hasOutput ? (
          <div className="mt-3 space-y-2">
            {output.stdout ? (
              <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800 dark:bg-emerald-500/8 dark:text-emerald-200">{output.stdout}</pre>
            ) : null}
            {output.stderr ? (
              <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">{output.stderr}</pre>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

function TerminalPanel({
  history,
  loading,
  cwd,
  input,
  setInput,
  onSubmit,
  onInputKeyDown,
  inputRef,
  terminalRef,
  onCopyOutput,
}) {
  return (
    <section className="relative flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">

      <div className="relative z-10 mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Command Console</h2>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">{cwd || '~'}</span>
      </div>

      <div ref={terminalRef} className="relative z-10 flex-1 space-y-3 overflow-y-auto pr-1">
        {history.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <p className="text-slate-700 dark:text-slate-200">Ask anything to your AI terminal.</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-500 dark:text-slate-400">
              <li>Create a folder, setup venv, install pandas</li>
              <li>Run direct commands like <code>ls</code>, <code>cd ..</code>, <code>pwd</code></li>
              <li>Ctrl+L to clear, Ctrl+C to cancel active request</li>
            </ul>
          </div>
        ) : null}

        {history.map((entry) => (
          <div key={entry.id} className="animate-in-up">
            <CommandBubble entry={entry} onCopyOutput={onCopyOutput} />
          </div>
        ))}

        {loading ? (
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <span className="inline-block h-2.5 w-2.5 animate-spin rounded-full border-2 border-emerald-300 border-t-transparent" />
            <span>Executing command...</span>
          </div>
        ) : null}
      </div>

      <form onSubmit={onSubmit} className="relative z-10 mt-4">
        <div className="group flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 transition focus-within:border-emerald-400 dark:border-slate-700 dark:bg-slate-800">
          <span className="rounded-lg bg-emerald-100 px-2 py-1 text-xs text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200">$</span>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Ask or run a command..."
            className="w-full bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
            spellCheck={false}
          />
          <span className="h-4 w-[2px] animate-caret rounded bg-emerald-400/80" />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-emerald-500 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Run
          </button>
        </div>
      </form>
    </section>
  )
}

export default TerminalPanel
