import axios from 'axios'
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

import { getCookie } from '../utils/csrfCookie'
import { DEV_BYPASS_ACCESS_TOKEN, isDevBypassAuth } from '../constants/devAuth'
import { SESSION_ACCESS_TOKEN } from '../constants/sessionAuth'
import { useAuthStore } from '../store/authStore'

// Единый axios-инстанс: baseURL, Bearer, refresh при 401.
const apiClient: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

function loginUrlWithNext(): string {
  const next = window.location.pathname + window.location.search
  return `/login?next=${encodeURIComponent(next)}`
}

// --- Интерцептор запросов ---
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken
    // Фиктивный токен dev-режима не посылаем — иначе 401 и лишние refresh.
    if (token && token !== DEV_BYPASS_ACCESS_TOKEN && token !== SESSION_ACCESS_TOKEN) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Session cookie + POST без заголовка даёт 403 CSRF (например /api/vector/search/).
    const method = (config.method ?? 'get').toUpperCase()
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrf = getCookie('csrftoken')
      if (csrf) {
        config.headers['X-CSRFToken'] = csrf
      }
    }
    // FormData: убрать application/json, иначе DRF вернёт 415 (multipart без boundary)
    if (config.data instanceof FormData) {
      config.headers.set('Content-Type', false)
    }
    return config
  },
  (error: AxiosError) => Promise.reject(error),
)

// --- Интерцептор ответов ---
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,

  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status

    if (status !== 401 || !original) {
      return Promise.reject(error)
    }

    const url = original.url ?? ''
    if (url.includes('/api/auth/login/')) {
      return Promise.reject(error)
    }

    if (!isDevBypassAuth()) {
      useAuthStore.getState().clearSession()
      // persist пишет localStorage асинхронно. Без сброса старая сессия
      // переживает переход и LoginPage снова уводит на закрытую страницу.
      useAuthStore.persist.clearStorage()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign(loginUrlWithNext())
      }
    }
    return Promise.reject(error)
  },
)

export default apiClient
