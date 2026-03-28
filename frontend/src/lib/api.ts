import axios from 'axios'

/**
 * Custom error class for API errors with structured information
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly data?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const api = axios.create({
  baseURL: '/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract error details from axios error structure
    const status = error.response?.status ?? 0
    const data = error.response?.data
    
    let message: string
    
    if (status === 400) {
      // Bad Request - validation errors
      message = data?.detail || 'Invalid request parameters'
    } else if (status === 401) {
      // Unauthorized
      message = 'Authentication required'
    } else if (status === 403) {
      // Forbidden
      message = 'Access denied'
    } else if (status === 404) {
      // Not Found
      message = data?.detail || 'Resource not found'
    } else if (status === 409) {
      // Conflict
      message = data?.detail || 'Conflict - operation cannot be completed'
    } else if (status >= 500) {
      // Server errors
      message = 'Server error occurred. Please try again later.'
    } else {
      // Network or other errors
      message = error.message || 'An unexpected error occurred'
    }
    
    const apiError = new ApiError(message, status, data)
    return Promise.reject(apiError)
  },
)

export default api
