import { hasMeaningfulQueryFilters, LIST_PAGE_SORT_PAGINATION_KEYS } from '../listPageSearchParams'

/** Класс модификатора для `.interview-type-badge` по коду типа собеседования (API). */
export function interviewTypeBadgeClass(interviewType: string): string {
  switch (interviewType) {
    case 'cancelled':
      return 'interview-type-badge--danger'
    case 'final':
      return 'interview-type-badge--success'
    case 'tech':
    case 'tech_questionnaire':
      return 'interview-type-badge--tech'
    case 'hr':
      return 'interview-type-badge--hr'
    case 'screening':
      return 'interview-type-badge--screening'
    case 'mock':
    case 'test':
      return 'interview-type-badge--muted'
    default:
      return 'interview-type-badge--default'
  }
}

/** Есть ли в query что-то кроме пагинации и сортировки. */
export function hasActiveListFilters(searchParams: URLSearchParams): boolean {
  return hasMeaningfulQueryFilters(searchParams, LIST_PAGE_SORT_PAGINATION_KEYS)
}
