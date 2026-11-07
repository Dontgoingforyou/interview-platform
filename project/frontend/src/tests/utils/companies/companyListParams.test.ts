import { describe, expect, it } from 'vitest'

import {
  COMPANY_LIST_MEANINGFUL_FILTER_IGNORE,
  COMPANY_LIST_META_KEYS,
  parseCompanyListFromSearchParams,
} from '../../../utils/companies/companyListParams'

describe('parseCompanyListFromSearchParams', () => {
  it('дефолты без query', () => {
    expect(parseCompanyListFromSearchParams(new URLSearchParams())).toEqual({
      q: '',
      bigtech: '',
      sort: 'interviews',
      page: 1,
    })
  })

  it('читает q, bigtech, sort и page', () => {
    const sp = new URLSearchParams('q=яндекс&bigtech=1&sort=-name&page=3')
    expect(parseCompanyListFromSearchParams(sp)).toEqual({
      q: 'яндекс',
      bigtech: '1',
      sort: '-name',
      page: 3,
    })
  })

  it('игнорирует невалидный sort и bigtech; page < 1 → 1', () => {
    const sp = new URLSearchParams('bigtech=yes&sort=weird&page=0')
    const f = parseCompanyListFromSearchParams(sp)
    expect(f.bigtech).toBe('')
    expect(f.sort).toBe('interviews')
    expect(f.page).toBe(1)
  })

  it('meta keys и ignore для фильтров заданы', () => {
    expect(COMPANY_LIST_META_KEYS.has('page')).toBe(true)
    expect(COMPANY_LIST_MEANINGFUL_FILTER_IGNORE).toContain('sort')
  })
})
