import type { AuthUser } from '../store/authStore'
import { SESSION_ACCESS_TOKEN } from '../constants/sessionAuth'
import apiClient from './client'

export type LoginResult = {
  expires_in: number
  user: AuthUser
  redirect_after_login?: string
}

export async function loginWithPassword(username: string, password: string): Promise<LoginResult> {
  const { data } = await apiClient.post<LoginResult>('/api/auth/login/', { username, password })
  return data
}

export { SESSION_ACCESS_TOKEN }
