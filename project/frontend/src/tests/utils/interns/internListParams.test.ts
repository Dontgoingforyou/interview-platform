import { describe, expect, it } from 'vitest'

import type { InternListFilters } from '../../../types/intern'
import {
  buildInternListParams,
  parseInternListFromSearchParams,
} from '../../../utils/interns/internListParams'

describe('buildInternListParams', () => {
  it('пустой и полный набор', () => {
    expect(buildInternListParams({})).toEqual({})
    const filters: InternListFilters = {
      page: 2,
      q: 'иван',
      status: 'активный',
      manager: 'm@x.ru',
      direction_id: 3,
      group: 'a',
      order_by: 'full_name',
      order_dir: 'asc',
    }
    expect(buildInternListParams(filters)).toEqual(filters)
  })
})

describe('parseInternListFromSearchParams', () => {
  it('дефолты и разбор query', () => {
    const empty = parseInternListFromSearchParams(new URLSearchParams())
    expect(empty).toEqual({ page: 1, order_by: 'id', order_dir: 'desc' })

    const sp = new URLSearchParams(
      'page=2&q=x&status=оффер&manager=a@b.ru&direction_id=5&group=g1&order_by=name&order_dir=asc',
    )
    expect(parseInternListFromSearchParams(sp)).toMatchObject({
      page: 2,
      q: 'x',
      status: 'оффер',
      manager: 'a@b.ru',
      direction_id: 5,
      group: 'g1',
      order_by: 'name',
      order_dir: 'asc',
    })

    const bad = parseInternListFromSearchParams(
      new URLSearchParams('page=0&direction_id=x&order_dir=side'),
    )
    expect(bad.page).toBe(1)
    expect(bad.direction_id).toBeUndefined()
    expect(bad.order_dir).toBe('desc')
  })
})
