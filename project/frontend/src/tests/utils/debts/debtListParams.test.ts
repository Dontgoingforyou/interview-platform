import { describe, expect, it } from 'vitest'

import type { DebtListFilters } from '../../../types/debt'
import {
  DEBT_LIST_DEFAULT_ORDER_BY,
  DEBT_LIST_DEFAULT_ORDER_DIR,
  buildDebtListParams,
  parseDebtListFromSearchParams,
} from '../../../utils/debts/debtListParams'

describe('buildDebtListParams', () => {
  it('пустой объект без фильтров', () => {
    expect(buildDebtListParams({})).toEqual({})
  })

  it('передаёт заполненные поля', () => {
    const filters: DebtListFilters = {
      page: 2,
      page_size: 50,
      q: 'иван',
      direction: 3,
      payment_status: 'paying',
      intern_id: 9,
      not_paid_filter: '1',
      act_date_filter: 'month',
      act_date_from: '2025-01-01',
      act_date_to: '2025-12-31',
      order_by: 'balance',
      order_dir: 'asc',
    }
    expect(buildDebtListParams(filters)).toEqual(filters)
  })
})

describe('parseDebtListFromSearchParams', () => {
  it('дефолты сортировки', () => {
    const f = parseDebtListFromSearchParams(new URLSearchParams())
    expect(f.page).toBe(1)
    expect(f.order_by).toBe(DEBT_LIST_DEFAULT_ORDER_BY)
    expect(f.order_dir).toBe(DEBT_LIST_DEFAULT_ORDER_DIR)
  })

  it('читает фильтры и игнорирует битый order_dir / page', () => {
    const sp = new URLSearchParams(
      'page=2&q=x&direction=5&payment_status=paying&not_paid_filter=1&act_date_filter=custom&act_date_from=2025-01-01&act_date_to=2025-02-01&order_by=name&order_dir=asc',
    )
    const f = parseDebtListFromSearchParams(sp)
    expect(f.page).toBe(2)
    expect(f.q).toBe('x')
    expect(f.direction).toBe(5)
    expect(f.payment_status).toBe('paying')
    expect(f.order_dir).toBe('asc')

    const bad = parseDebtListFromSearchParams(new URLSearchParams('page=abc&direction=x&order_dir=sideways'))
    expect(bad.page).toBe(1)
    expect(bad.direction).toBeUndefined()
    expect(bad.order_dir).toBe(DEBT_LIST_DEFAULT_ORDER_DIR)
  })
})
