import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import API_CONFIG from './config/api'
import './App.css'

function App() {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [cwd, setCwd] = useState('') // Current working directory
  const terminalRef = useRef(null)
  const inputRef = useRef(null)

  // Fetch initial CWD when component mounts
  useEffect(() => {
    const fetchInitialCwd = async () => {
      try {
        // Make a simple request to get the current directory
        const response = await axios.post(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TERMINAL_EXECUTE}`,
          {
            command: 'pwd',
            cwd: cwd
          }
        )
        
        // Set CWD from response or default to ~
        console.log('Initial CWD response:', response.data)
        if (response.data?.new_cwd) {
          setCwd(response.data.new_cwd)
        } else {
          setCwd('~')
        }
      } catch (err) {
        console.error('Failed to fetch initial CWD:', err)
        setCwd('~')
      }
    }
    
    fetchInitialCwd()
  }, [])

  // Auto-scroll to bottom when history updates
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [history, loading])

  // Focus input when clicking anywhere in terminal
  const handleTerminalClick = () => {
    inputRef.current?.focus()
  }

  // Keep input focused
  useEffect(() => {
    inputRef.current?.focus()
  }, [loading])

  const handleKeyDown = async (e) => {
    if (e.key === 'Enter' && !loading && input.trim()) {
      e.preventDefault()
      const userInput = input.trim()
      setInput('')
      setLoading(true)

      // Add user input to history
      setHistory(prev => [...prev, {
        type: 'input',
        content: userInput,
        cwd: cwd,
        timestamp: new Date().toISOString()
      }])

      // Check if it's a direct command (ls, cd, pwd) - execute directly without AI
      const directCommands = ['ls', 'pwd', 'cd']
      const commandWord = userInput.split(' ')[0]
      const isDirectCommand = directCommands.includes(commandWord)

      try {
        let response;
        
        if (isDirectCommand) {
          // Execute direct commands without AI processing
          response = await axios.post(
            `${API_CONFIG.BASE_URL}/terminal/execute`,
            {
              command: userInput,
              cwd: cwd
            },
            {
              timeout: API_CONFIG.TIMEOUT,
              headers: {
                'Content-Type': 'application/json'
              }
            }
          );
        } else {
          // Use AI for natural language commands
          response = await axios.post(
            `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TERMINAL_RUN}`,
            {
              input: userInput,
              execute: false,
              context: {
                os: window.electronAPI?.platform || 'linux',
                shell: 'bash',
                cwd: cwd
              }
            },
            {
              timeout: API_CONFIG.TIMEOUT,
              headers: {
                'Content-Type': 'application/json'
              }
            }
          );
        }
        
        console.log('API response:', response.data)
        
        // Update CWD if provided by backend
        if (response.data.new_cwd) {
          setCwd(response.data.new_cwd)
        }
        
        // Add AI response to history
        setHistory(prev => [...prev, {
          type: 'output',
          content: response.data,
          timestamp: new Date().toISOString()
        }])
      } catch (err) {
        console.error('Error calling API:', err)
        const errorMessage = err.response?.data?.error || err.message || 'Failed to connect to backend'
        setHistory(prev => [...prev, {
          type: 'error',
          content: errorMessage,
          timestamp: new Date().toISOString()
        }])
      } finally {
        setLoading(false)
      }
    }

    // Handle Ctrl+L to clear terminal
    if (e.ctrlKey && e.key === 'l') {
      e.preventDefault()
      setHistory([])
    }

    // Handle Ctrl+C to cancel loading
    if (e.ctrlKey && e.key === 'c' && loading) {
      e.preventDefault()
      setLoading(false)
    }
  }

  const getSafetyColor = (level) => {
    switch (level) {
      case 'safe': return 'text-green-400'
      case 'caution': return 'text-yellow-400'
      case 'danger': return 'text-orange-400'
      case 'blocked': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="h-screen bg-black text-green-400 flex flex-col font-mono overflow-hidden">
      {/* Terminal Header */}
      <header className="bg-black border-b border-green-900 px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          
          <span className="ml-4 text-sm text-green-500">AI Terminal - bash</span>
        </div>
        <div className="text-xs text-green-700">
          <span className="text-green-600">Ctrl+L</span> clear | <span className="text-green-600">Ctrl+C</span> cancel
        </div>
      </header>

      {/* Terminal Area */}
      <div 
        ref={terminalRef}
        onClick={handleTerminalClick}
        className="flex-1 overflow-y-auto p-4 cursor-text relative"
      >
        {/* Welcome Message */}
        {history.length === 0 && !loading && (
          <div className="text-green-600 space-y-1 mb-4">
            <p>AI Terminal v1.0.0</p>
            <p className="text-green-700">Type natural language commands and press Enter.</p>
            <p className="text-green-700 mt-2">Examples:</p>
            <p className="text-green-500 ml-2">install fastapi</p>
            <p className="text-green-500 ml-2">create a react app</p>
            <p className="text-green-500 ml-2">list all python files</p>
            <p className="text-green-700 mt-2">---</p>
          </div>
        )}

        {/* Terminal History */}
        {history.map((entry, index) => (
          <div key={index} className="mb-3">
            {entry.type === 'input' && (
              <div className="flex items-start gap-2">
                <span className="text-green-700 select-none">{entry.cwd || '~'}</span>
                <span className="text-green-500 select-none">$</span>
                <span className="text-green-400">{entry.content}</span>
              </div>
            )}

            {entry.type === 'output' && (
              <div className="ml-4 mt-1 space-y-1.5 text-sm">
                <div className="flex items-baseline gap-2">
                  <span className="text-green-700 text-xs">→</span>
                  <code className="text-green-400 font-bold">{entry.content.command}</code>
                </div>
                
                <div className="ml-4 text-green-500">
                  {entry.content.explanation}
                </div>

                {/* Display command execution output */}
                {entry.content.execution_result && (
                  <div className="ml-4 mt-2">
                    {entry.content.execution_result.stdout && (
                      <pre className="text-green-400 whitespace-pre-wrap break-words text-xs">
                        {entry.content.execution_result.stdout}
                      </pre>
                    )}
                    {entry.content.execution_result.stderr && (
                      <pre className="text-red-400 whitespace-pre-wrap break-words text-xs">
                        {entry.content.execution_result.stderr}
                      </pre>
                    )}
                  </div>
                )}

                <div className="ml-4 flex gap-6 text-xs text-green-700">
                  <span>intent: <span className="text-green-500">{entry.content.intent}</span></span>
                  <span>safety: <span className={getSafetyColor(entry.content.safety_level)}>{entry.content.safety_level}</span></span>
                </div>

                {entry.content.warning && (
                  <div className="ml-4 border-l-2 border-yellow-600 pl-2 py-1 text-yellow-500 text-xs">
                    ⚠ {entry.content.warning}
                  </div>
                )}

                {entry.content.alternative_commands?.length > 0 && (
                  <div className="ml-4 mt-2 text-xs">
                    <span className="text-green-700">alternatives:</span>
                    {entry.content.alternative_commands.map((cmd, i) => (
                      <div key={i} className="ml-2 text-green-600">• {cmd}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {entry.type === 'error' && (
              <div className="ml-4 text-red-500 text-sm border-l-2 border-red-900 pl-2">
                error: {entry.content}
              </div>
            )}
          </div>
        ))}

        {/* Loading State */}
        {loading && (
          <div className="ml-4 flex items-center gap-2 text-green-600 text-sm">
            <span className="animate-pulse">▮</span>
            <span>processing...</span>
          </div>
        )}

        {/* Active Input Line */}
        {!loading && (
          <div className="flex items-start gap-2">
            <span className="text-green-700 select-none">{cwd}</span>
            <span className="text-green-500 select-none">$</span>
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full bg-transparent border-none outline-none text-green-400 caret-green-400"
                autoFocus
                spellCheck={false}
              />
              {!input && (
                <span className="absolute left-0 top-0 text-green-800 pointer-events-none select-none">
                  type command here...
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* Created by credit - bottom right */}
        <div className="fixed bottom-4 right-4 text-xs text-green-800 pointer-events-none select-none">
          Developed by Abhishek
        </div>
      </div>
    </div>
  )
}

export default App
