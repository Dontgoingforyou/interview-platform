/** Максимальный размер видео для загрузки с портала (10 ГБ), синхрон с бэкендом. */
export const INTERN_PORTAL_MAX_VIDEO_BYTES = 10 * 1024 * 1024 * 1024

/** Допустимые расширения — синхрон с interns_portal.constants.ALLOWED_VIDEO_EXTENSIONS */
export const INTERN_PORTAL_VIDEO_ACCEPT = '.mp4,.mov,.avi,.mkv,.webm,.flv,.wmv'

/**
 * Таймаут axios при POST загрузки видео (мс).
 * 0 — без лимита на клиенте (иначе крупные файлы обрываются раньше ответа сервера: общий timeout apiClient 30 с).
 */
export const INTERN_PORTAL_UPLOAD_TIMEOUT_MS = 0
