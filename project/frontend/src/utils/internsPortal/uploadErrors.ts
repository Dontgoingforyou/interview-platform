import type { AxiosError } from 'axios'

/** Сообщение об ошибке POST загрузки видео. */
export function internPortalUploadErrorMessage(error: unknown): string {
  const ax = error as AxiosError<{ error?: string; detail?: string }>
  const status = ax.response?.status
  const serverMsg = ax.response?.data?.error ?? ax.response?.data?.detail

  if (status === 409) {
    return serverMsg ?? 'Загрузка уже выполняется. Дождитесь завершения перед повторной отправкой.'
  }
  if (status === 429) {
    return 'Превышен лимит загрузок (10 в час). Попробуйте позже.'
  }
  if (typeof serverMsg === 'string' && serverMsg.trim()) {
    return serverMsg
  }
  return 'Не удалось отправить файл. Проверьте сеть и размер файла.'
}

/** Текст ошибки из поллинга Celery (FAILURE). */
export function internPortalCeleryFailureMessage(status: string | undefined): string {
  const trimmed = status?.trim()
  if (!trimmed) {
    return 'Ошибка загрузки в облачное хранилище'
  }
  if (trimmed.length > 300) {
    return `${trimmed.slice(0, 300)}…`
  }
  return trimmed
}
