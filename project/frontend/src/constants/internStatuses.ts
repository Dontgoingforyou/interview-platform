/**
 * Статусы и типы обучения студентов для UI.
 * Строковые значения должны совпадать с `core.constants` / `interns.models.Intern` в бэкенде.
 */
export const INTERN_STATUS_ACTIVE = 'активный'
export const INTERN_STATUS_LEFT = 'ушел'
export const INTERN_STATUS_OFFER = 'оффер'

export const INTERN_STATUS_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'Все' },
  { value: INTERN_STATUS_ACTIVE, label: 'Активный' },
  { value: INTERN_STATUS_LEFT, label: 'Ушёл' },
  { value: INTERN_STATUS_OFFER, label: 'Оффер' },
]

export const INTERN_TRAINING_OPTIONS: { value: string; label: string }[] = [
  { value: 'internal', label: 'Внутреннее обучение' },
  { value: 'outstaff', label: 'Аутстафф' },
  { value: 'external', label: 'Во вне' },
  { value: 'external_or_outstaff', label: 'Во вне / аутстафф' },
]

export const INTERN_MANUAL_STATUS_FORM_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'По умолчанию (активный)' },
  { value: INTERN_STATUS_ACTIVE, label: 'Активный' },
  { value: INTERN_STATUS_LEFT, label: 'Ушёл' },
  { value: INTERN_STATUS_OFFER, label: 'Оффер' },
]
