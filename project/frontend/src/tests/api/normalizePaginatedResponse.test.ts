import { describe, expect, it } from 'vitest'

import { normalizePaginatedResponse } from '../../api/normalizePaginatedResponse'

describe('normalizePaginatedResponse', () => {
  it('оборачивает массив', () => {
    const data = [{ id: 1 }, { id: 2 }]
    expect(normalizePaginatedResponse(data)).toEqual({
      count: 2,
      next: null,
      previous: null,
      results: data,
    })
  })

  it('оставляет пагинированный ответ', () => {
    const paginated = {
      count: 100,
      next: 'http://x',
      previous: null,
      results: [{ id: 1 }],
    }
    expect(normalizePaginatedResponse(paginated)).toBe(paginated)
  })
})
