import { KEYCLOAK_MANAGER_GROUPS } from '../../constants/keycloakGroups'
import type { AuthUser } from '../../store/authStore'
import type { InterviewListItem } from '../../types/interview'
import { isYandexDiskPublicFileUrl } from '../yandexDiskUrl'

function hasTranscriptionSourceInRow(row: InterviewListItem): boolean {
  if (row.transcription_media_url?.trim()) {
    return true
  }
  if (row.video_link?.trim()) {
    return true
  }
  const l = row.link?.trim()
  if (l && isYandexDiskPublicFileUrl(l)) {
    return true
  }
  const il = row.interview_link?.trim()
  return Boolean(il && isYandexDiskPublicFileUrl(il))
}

/**
 * Показывать кнопки транскрипции: непустой transcription_media_url с API, запасной разбор
 * video_link / Я.Диск в link и interview_link, либо уже есть InterviewTranscription (статус ≠ none).
 */
export function showTranscriptionControls(row: InterviewListItem): boolean {
  const st = row.transcription_status
  if (st && st !== 'none') {
    return true
  }
  return hasTranscriptionSourceInRow(row)
}

/**
 * Доступ к просмотру/кнопкам транскрипции.
 */
export function mayAccessInterviewTranscription(
  user: AuthUser | null,
  row: InterviewListItem,
): boolean {
  if (!user) {
    return false
  }
  const role = user.manager_role
  if (role === 'admin') {
    return true
  }
  if (role === 'hr' || role === 'outstaff' || role === 'mentor') {
    return true
  }
  if (role === 'student' || role === 'no_access') {
    return false
  }
  if (role !== 'manager') {
    return false
  }
  const groups = new Set(user.groups)
  let inManagerGroup = false
  for (const g of groups) {
    if (KEYCLOAK_MANAGER_GROUPS.has(g)) {
      inManagerGroup = true
      break
    }
  }
  if (!inManagerGroup) {
    return false
  }
  const email = user.email
  if (!email) {
    return false
  }
  if (row.manager_email === email) {
    return true
  }
  return false
}
