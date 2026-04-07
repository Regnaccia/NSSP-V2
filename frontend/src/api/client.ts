/**
 * Client HTTP per le chiamate al backend V2.
 *
 * Aggiunge automaticamente l'header Authorization Bearer
 * se il token è presente nello store.
 */

import axios from 'axios'
import { useAuthStore } from '@/app/authStore'

export const apiClient = axios.create({
  baseURL: '/api',
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(err)
  }
)
