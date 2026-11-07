import { describe, expect, it } from 'vitest'

import {
  applyTableSortToSearchParams,
  hasMeaningfulQueryFilters,
  withClonedSearchParams,
} from '../../utils/listPageSearchParams'

describe('hasMeaningfulQueryFilters', () => {
  it('игнорирует page, order_by, order_dir', () => {
    const sp = new URLSearchParams('page=2&order_by=id&order_dir=desc')
    expect(hasMeaningfulQueryFilters(sp)).toBe(false)
  })

  it('видит прочие ключи', () => {
    const sp = new URLSearchParams('page=1&q=тест')
    expect(hasMeaningfulQueryFilters(sp)).toBe(true)
  })
})

describe('withClonedSearchParams', () => {
  it('не мутирует исходный объект', () => {
    const cur = new URLSearchParams('a=1')
    const next = withClonedSearchParams(cur, (p) => {
      p.set('b', '2')
    })
    expect(cur.get('b')).toBeNull()
    expect(next.get('a')).toBe('1')
    expect(next.get('b')).toBe('2')
  })
})

describe('applyTableSortToSearchParams', () => {
  it('при новой колонке задаёт направление', () => {
    const p = new URLSearchParams('page=3')
    applyTableSortToSearchParams(p, 'date', 'desc')
    expect(p.get('order_by')).toBe('date')
    expect(p.get('order_dir')).toBe('desc')
    expect(p.get('page')).toBe('1')
  })

  it('переключает направление той же колонки', () => {
    const p = new URLSearchParams('order_by=date&order_dir=desc')
    applyTableSortToSearchParams(p, 'date', 'desc')
    expect(p.get('order_dir')).toBe('asc')
  })
})
