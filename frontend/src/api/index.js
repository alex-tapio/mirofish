import axios from 'axios'

const STORAGE_KEY = 'mirofish_settings'

/**
 * Get saved user settings from localStorage
 */
function getUserSettings() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

// Create axios instance
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  timeout: 300000, // 5 minute timeout (LLM operations can be slow)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor — inject user's LLM settings into every request
service.interceptors.request.use(
  config => {
    const settings = getUserSettings()
    if (settings) {
      config.headers['X-LLM-API-Key'] = settings.apiKey || ''
      config.headers['X-LLM-Base-URL'] = settings.baseUrl || ''
      config.headers['X-LLM-Model'] = settings.model || ''
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  response => {
    const res = response.data

    if (!res.success && res.success !== undefined) {
      console.error('API Error:', res.error || res.message || 'Unknown error')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }

    return res
  },
  error => {
    console.error('Response error:', error)

    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }

    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection')
    }

    return Promise.reject(error)
  }
)

// Request function with retry
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error

      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
