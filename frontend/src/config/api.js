// src/config/api.js

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  ENDPOINTS: {
    TERMINAL_RUN: '/terminal/run',
    TERMINAL_EXECUTE: '/terminal/execute',  
    TERMINAL_FIX: '/terminal/fix',
    HEALTH: '/terminal/health',
  },
  TIMEOUT: 30000, // 30 seconds
};

export default API_CONFIG;
