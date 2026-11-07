/**
 * Значения `interview_type` для UI.
 * Коды и подписи должны совпадать с `interviews.models.Interview.INTERVIEW_TYPES` / `core.constants` в бэкенде
 * (единого автогенерируемого источника в репозитории нет — при изменении модели править и этот файл).
 */
export const INTERVIEW_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'screening', label: 'Скрининг' },
  { value: 'tech', label: 'Техническое собеседование' },
  { value: 'hr', label: 'HR собеседование' },
  { value: 'final', label: 'Финальное собеседование' },
  { value: 'mock', label: 'МОК собеседование' },
  { value: 'test', label: 'Тестовое задание' },
  { value: 'tech_questionnaire', label: 'Анкета с большим кол-вом технички' },
  { value: 'cancelled', label: 'НЕ СОСТОЯЛОСЬ' },
]

export const INTERVIEW_FORMAT_OPTIONS: { value: string; label: string }[] = [
  { value: 'online', label: 'Онлайн' },
  { value: 'office', label: 'Офис' },
  { value: 'phone', label: 'Телефонный звонок' },
]
