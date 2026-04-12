// src/config/api.js

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  ENDPOINTS: {
    TERMINAL_RUN: '/terminal/run',
    TERMINAL_EXECUTE: '/terminal/execute',  
    TERMINAL_FIX: '/terminal/fix',
    HEALTH: '/terminal/health',
  },
  TIMEOUT: 45000, // Increased to 45 seconds to handle slower LLM API responses and system installations
};

export default API_CONFIG;
