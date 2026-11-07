/** Пагинированный ответ API: count, next, previous, results. */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** Направление сортировки. */
export type OrderDir = 'asc' | 'desc'

/**
 * Стандартная опция для react-select: { value, label }.
 *
 * Аналог кортежа (value, display) в Django choices.
 * Используется во всех фильтрах и формах вместо inline-типов.
 *
 * @example
 *   const options: SelectOption<number>[] = [{ value: 1, label: 'Бэкенд' }]
 *   const stringOpts: SelectOption[] = [{ value: 'active', label: 'Активный' }]
 */
export interface SelectOption<T extends string | number = string> {
  value: T
  label: string
}
