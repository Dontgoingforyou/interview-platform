import { describe, expect, it } from 'vitest'

import type { DeveloperListFilters } from '../../../types/developer'
import {
  DEVELOPER_LIST_DEFAULT_ORDER_BY,
  DEVELOPER_LIST_DEFAULT_ORDER_DIR,
  buildDeveloperListParams,
  buildDeveloperTableExportParams,
  parseDeveloperListFromSearchParams,
} from '../../../utils/developers/developerListParams'

describe('buildDeveloperListParams', () => {
  it('page>1 и фильтры', () => {
    const filters: DeveloperListFilters = {
      page: 2,
      q: 'ivan',
      direction_id: 4,
      order_by: 'full_name',
      order_dir: 'asc',
    }
    expect(buildDeveloperListParams(filters)).toEqual({
      order_by: 'full_name',
      order_dir: 'asc',
      page: 2,
      q: 'ivan',
      direction_id: 4,
    })
    expect(buildDeveloperListParams({ ...filters, page: 1 })).not.toHaveProperty('page')
  })
})

describe('buildDeveloperTableExportParams', () => {
  it('без page', () => {
    expect(
      buildDeveloperTableExportParams({
        page: 3,
        q: 'x',
        direction_id: 1,
        order_by: 'interview_count',
        order_dir: 'desc',
      }),
    ).toEqual({
      q: 'x',
      direction_id: 1,
      order_by: 'interview_count',
      order_dir: 'desc',
    })
  })
})

describe('parseDeveloperListFromSearchParams', () => {
  it('дефолты и валидный order_by; direction alias', () => {
    const empty = parseDeveloperListFromSearchParams(new URLSearchParams())
    expect(empty.order_by).toBe(DEVELOPER_LIST_DEFAULT_ORDER_BY)
    expect(empty.order_dir).toBe(DEVELOPER_LIST_DEFAULT_ORDER_DIR)

    const sp = new URLSearchParams(
      'page=2&q=a&direction=7&order_by=last_activity&order_dir=asc',
    )
    const f = parseDeveloperListFromSearchParams(sp)
    expect(f.page).toBe(2)
    expect(f.direction_id).toBe(7)
    expect(f.order_by).toBe('last_activity')
    expect(f.order_dir).toBe('asc')

    const bad = parseDeveloperListFromSearchParams(new URLSearchParams('order_by=hack&order_dir=x'))
    expect(bad.order_by).toBe(DEVELOPER_LIST_DEFAULT_ORDER_BY)
    expect(bad.order_dir).toBe(DEVELOPER_LIST_DEFAULT_ORDER_DIR)
  })
})
