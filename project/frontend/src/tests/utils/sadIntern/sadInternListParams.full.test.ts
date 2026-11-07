import { describe, expect, it } from 'vitest'

import {
  SAD_INTERN_DEFAULT_ORDER_BY,
  SAD_INTERN_DEFAULT_ORDER_DIR,
  SAD_INTERN_LIST_META_KEYS,
  buildSadInternGroupedParams,
  buildSadInternOnProjectParams,
  parseSadInternGroupPages,
  parseSadInternListFromSearchParams,
  sadInternGroupedFilterKey,
} from '../../../utils/sadIntern/sadInternListParams'

describe('parseSadInternGroupPages', () => {
  it('берёт только page_* >= 1', () => {
    const sp = new URLSearchParams('page_5=2&page_none=1&q=x&page_bad=0&foo=1')
    expect(parseSadInternGroupPages(sp)).toEqual({ '5': 2, none: 1 })
  })
})

describe('parseSadInternListFromSearchParams', () => {
  it('дефолты и фильтры', () => {
    const empty = parseSadInternListFromSearchParams(new URLSearchParams())
    expect(empty.order_by).toBe(SAD_INTERN_DEFAULT_ORDER_BY)
    expect(empty.order_dir).toBe(SAD_INTERN_DEFAULT_ORDER_DIR)
    expect(empty.on_project_page).toBe(1)

    const sp = new URLSearchParams(
      'q=иван&status=rejected&direction=3&order_by=name&order_dir=asc&on_project_page=2',
    )
    expect(parseSadInternListFromSearchParams(sp)).toMatchObject({
      q: 'иван',
      status: 'rejected',
      direction: 3,
      order_by: 'name',
      order_dir: 'asc',
      on_project_page: 2,
    })

    const badDir = parseSadInternListFromSearchParams(new URLSearchParams('direction=x'))
    expect(badDir.direction).toBeUndefined()
  })
})

describe('buildSadInternOnProjectParams / filterKey', () => {
  const base = {
    order_by: 'days_waiting',
    order_dir: 'desc' as const,
    on_project_page: 2,
    q: 'a',
    status: 'rejected',
    direction: 5,
  }

  it('on_project params', () => {
    expect(buildSadInternOnProjectParams(base)).toEqual({
      on_project_page: 2,
      q: 'a',
      status: 'rejected',
      direction: 5,
    })
  })

  it('grouped params с direction и page>=1', () => {
    const p = buildSadInternGroupedParams(base, 10, { '5': 2, skip: 0 })
    expect(p.directions_offset).toBe(10)
    expect(p.direction).toBe(5)
    expect(p.page_5).toBe(2)
    expect(p).not.toHaveProperty('page_skip')
  })

  it('filterKey стабилен; meta keys заданы', () => {
    expect(JSON.parse(sadInternGroupedFilterKey(base))).toMatchObject({
      q: 'a',
      status: 'rejected',
      direction: 5,
    })
    expect(SAD_INTERN_LIST_META_KEYS.has('order_by')).toBe(true)
  })
})
