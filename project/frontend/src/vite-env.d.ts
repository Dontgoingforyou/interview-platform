/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DJANGO_ORIGIN?: string
  readonly VITE_SPA_REDIRECT_URI?: string
  /** Только dev: обход входа, фиктивный пользователь (см. constants/devAuth.ts). */
  readonly VITE_DEV_BYPASS_AUTH?: string
  /** Только dev: admin | hr | manager — сценарий меню. */
  readonly VITE_DEV_MOCK_ROLE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
