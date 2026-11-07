import type { Paginated } from '../types/common'

/**
 * DRF может вернуть массив без оболочки пагинации — приводим к единому виду.
 */
export function normalizePaginatedResponse<T>(data: Paginated<T> | T[]): Paginated<T> {
  if (Array.isArray(data)) {
    return {
      count: data.length,
      next: null,
      previous: null,
      results: data,
    }
  }
  return data
}
