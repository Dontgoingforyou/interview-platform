/**
 * Сессия локального входа: access в памяти, refresh в httpOnly cookie на бэкенде.
 * В localStorage persist — только user и expiresAt (не access/refresh).
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AuthUser {
  email: string
  username: string
  full_name: string
  manager_role: string
  groups: string[]
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  expiresAt: number | null
  user: AuthUser | null
  setSession: (payload: {
    access_token: string
    refresh_token?: string
    expires_in: number
    user: AuthUser
  }) => void
  clearSession: () => void
  updateTokens: (payload: {
    access_token: string
    refresh_token?: string
    expires_in?: number
  }) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      user: null,
      setSession: (payload) =>
        set({
          accessToken: payload.access_token,
          refreshToken: null,
          expiresAt: Date.now() + payload.expires_in * 1000,
          user: payload.user,
        }),
      clearSession: () =>
        set({ accessToken: null, refreshToken: null, expiresAt: null, user: null }),
      updateTokens: (payload) =>
        set((s) => ({
          accessToken: payload.access_token,
          refreshToken: null,
          expiresAt:
            payload.expires_in !== undefined
              ? Date.now() + payload.expires_in * 1000
              : s.expiresAt,
        })),
    }),
    {
      name: 'interview-management-auth',
      partialize: (state) => ({
        expiresAt: state.expiresAt,
        user: state.user,
        accessToken: state.accessToken,
      }),
    },
  ),
)
