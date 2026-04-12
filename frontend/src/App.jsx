import { useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'
import API_CONFIG from './config/api'
import Navbar from './components/Navbar'
import TerminalPanel from './components/TerminalPanel'
import AIPanel from './components/AIPanel'
import './App.css'

function App() {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [cwd, setCwd] = useState('~')
  const [theme, setTheme] = useState(() => localStorage.getItem('ai-terminal-theme') || 'dark')
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [commandHistory, setCommandHistory] = useState([])
  const [historyCursor, setHistoryCursor] = useState(-1)

  const terminalRef = useRef(null)
  const inputRef = useRef(null)
  const activeRequestControllerRef = useRef(null)

  const runtimeStatus = loading
    ? 'running'
    : connectionStatus === 'connected'
      ? 'idle'
      : connectionStatus

  const latestOutput = useMemo(
    () => [...history].reverse().find((entry) => entry.type === 'output'),
    [history]
  )
  const latestError = useMemo(
    () => [...history].reverse().find((entry) => entry.type === 'error'),
    [history]
  )

  const createEntry = (type, payload) => ({
    id: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    timestamp: new Date().toISOString(),
    ...payload,
  })

  const normalizeCommandInput = (value) => {
    const trimmed = value.trim()
    if (trimmed === 'cd..') return 'cd ..'
    if (/^cd\.\.(\s|$)/i.test(trimmed)) {
      return trimmed.replace(/^cd\.\./i, 'cd ..')
    }
    return trimmed
  }

  const isDirectShellCommand = (value) => {
    const directCommands = [
      'ls', 'pwd', 'cd', 'mkdir', 'touch', 'cat', 'echo', 'cp', 'mv', 'rm',
      'find', 'grep', 'head', 'tail', 'which', 'whoami', 'python', 'pip',
      'npm', 'node', 'git', 'docker', 'docker-compose', 'pnpm', 'yarn', 'make'
    ]

    const normalized = normalizeCommandInput(value)
    const commandWord = normalized.split(' ')[0].toLowerCase()
    return directCommands.includes(commandWord)
  }

  const normalizeResponse = (data, command) => ({
    intent: data?.intent || 'run_command',
    command: data?.command || command,
    explanation: data?.explanation || 'Command executed',
    safety: data?.safety || 'safe',
    warnings: data?.warnings || [],
    plan: data?.plan || [],
    execution_result: data?.execution_result || null,
    new_cwd: data?.new_cwd || cwd,
  })

  const copyToClipboard = async (content) => {
    if (!content) return
    try {
      await navigator.clipboard.writeText(content)
    } catch (error) {
      setHistory((prev) => [
        ...prev,
        createEntry('error', { content: `Failed to copy: ${error.message}` }),
      ])
    }
  }

  const runHealthCheck = async () => {
    try {
      await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`, { timeout: 3000 })
      setConnectionStatus('connected')
    } catch {
      setConnectionStatus('disconnected')
    }
  }

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('ai-terminal-theme', theme)
  }, [theme])

  // Fetch initial CWD when component mounts
  useEffect(() => {
    const fetchInitialCwd = async () => {
      try {
        // Make a simple request to get the current directory
        const response = await axios.post(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TERMINAL_EXECUTE}`,
          {
            command: 'pwd',
            cwd: '~'
          }
        )
        
        // Set CWD from response or default to ~
        if (response.data?.new_cwd) {
          setCwd(response.data.new_cwd)
        } else {
          setCwd('~')
        }
        setConnectionStatus('connected')
      } catch (err) {
        console.error('Failed to fetch initial CWD:', err)
        setCwd('~')
        setConnectionStatus('disconnected')
      }
    }
    
    fetchInitialCwd()
    runHealthCheck()
    const interval = setInterval(runHealthCheck, 10000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to bottom when history updates
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [history, loading])

  // Keep input focused
  useEffect(() => {
    inputRef.current?.focus()
  }, [loading])

  const executeCommand = async () => {
    if (loading || !input.trim()) return

    const normalizedInput = normalizeCommandInput(input)
    setInput('')
    setLoading(true)
    setConnectionStatus('running')
    setCommandHistory((prev) => [...prev, normalizedInput])
    setHistoryCursor(-1)

    setHistory((prev) => [...prev, createEntry('input', { content: normalizedInput, cwd })])
    const isDirectCommand = isDirectShellCommand(normalizedInput)

    try {
      const controller = new AbortController()
      activeRequestControllerRef.current = controller
      let response

      if (isDirectCommand) {
        response = await axios.post(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TERMINAL_EXECUTE}`,
          { command: normalizedInput, cwd },
          {
            timeout: API_CONFIG.TIMEOUT,
            signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      } else {
        response = await axios.post(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TERMINAL_RUN}`,
          {
            input: normalizedInput,
            execute: false,
            context: {
              os: window.electronAPI?.platform || 'linux',
              shell: 'bash',
              cwd,
            },
          },
          {
            timeout: API_CONFIG.TIMEOUT,
            signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      }

      const normalizedResponse = normalizeResponse(response.data, normalizedInput)
      if (normalizedResponse.new_cwd) {
        setCwd(normalizedResponse.new_cwd)
      }

      setHistory((prev) => [...prev, createEntry('output', { content: normalizedResponse })])
      setConnectionStatus('connected')
    } catch (err) {
      if (err?.code === 'ERR_CANCELED') {
        setHistory((prev) => [...prev, createEntry('error', { content: 'Command cancelled by user' })])
        return
      }

      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        (err.code === 'ECONNABORTED' ? 'Request timed out. Backend may be busy or unavailable.' : null) ||
        err.message ||
        'Failed to connect to backend'
      setHistory((prev) => [...prev, createEntry('error', { content: errorMessage })])
      setConnectionStatus('disconnected')
    } finally {
      activeRequestControllerRef.current = null
      setLoading(false)
    }
  }

  const handleInputKeyDown = async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      await executeCommand()
      return
    }

    if (e.key === 'ArrowUp' && commandHistory.length) {
      e.preventDefault()
      const nextCursor = historyCursor < 0 ? commandHistory.length - 1 : Math.max(0, historyCursor - 1)
      setHistoryCursor(nextCursor)
      setInput(commandHistory[nextCursor] || '')
      return
    }

    if (e.key === 'ArrowDown' && commandHistory.length) {
      e.preventDefault()
      if (historyCursor <= 0) {
        setHistoryCursor(-1)
        setInput('')
        return
      }
      const nextCursor = historyCursor + 1
      if (nextCursor >= commandHistory.length) {
        setHistoryCursor(-1)
        setInput('')
        return
      }
      setHistoryCursor(nextCursor)
      setInput(commandHistory[nextCursor] || '')
      return
    }

    // Handle Ctrl+L to clear terminal
    if (e.ctrlKey && e.key === 'l') {
      e.preventDefault()
      setHistory([])
      return
    }

    // Handle Ctrl+C to cancel loading
    if (e.ctrlKey && e.key === 'c' && loading) {
      e.preventDefault()
      if (activeRequestControllerRef.current) {
        activeRequestControllerRef.current.abort()
      }
      setLoading(false)
      setConnectionStatus('idle')
    }
  }

  return (
    <div className={`app-shell ${theme === 'dark' ? 'dark' : ''}`}>
      <div className="relative min-h-screen bg-slate-100 px-4 py-4 text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-100">
        <Navbar cwd={cwd} status={runtimeStatus} theme={theme} onToggleTheme={toggleTheme} />

        <main className="grid h-[calc(100vh-7.25rem)] grid-cols-1 gap-4 lg:grid-cols-[1.35fr_0.95fr]">
          <TerminalPanel
            history={history}
            loading={loading}
            cwd={cwd}
            input={input}
            setInput={setInput}
            onSubmit={(e) => {
              e.preventDefault()
              executeCommand()
            }}
            onInputKeyDown={handleInputKeyDown}
            inputRef={inputRef}
            terminalRef={terminalRef}
            onCopyOutput={copyToClipboard}
          />

          <AIPanel
            latestOutput={latestOutput?.content}
            latestError={latestError}
            loading={loading}
            onCopy={copyToClipboard}
          />
        </main>

        <div className="pointer-events-none fixed bottom-4 right-5 text-[11px] text-slate-500 dark:text-slate-400">
          Developed by Abhishek Kumbhar
        </div>
      </div>
    </div>
  )
}

export default App
