import { describe, expect, it } from 'vitest'

import {
  OFFER_LIST_DEFAULT_ORDER_BY,
  OFFER_LIST_DEFAULT_ORDER_DIR,
  buildOfferListParams,
  buildOfferMonthGroupsBaseParams,
  parseOfferListFromSearchParams,
} from '../../../utils/offers/offerListParams'

describe('offerListParams', () => {
  it('month groups: search из q', () => {
    expect(
      buildOfferMonthGroupsBaseParams({
        q: 'иван',
        direction_id: 2,
        year: 2025,
        month: 3,
        intern_id: 9,
        order_by: 'year',
        order_dir: 'desc',
      }),
    ).toEqual({
      search: 'иван',
      direction_id: 2,
      year: 2025,
      month: 3,
      intern_id: 9,
    })
  })

  it('list params добавляет page и sort', () => {
    expect(
      buildOfferListParams({
        page: 2,
        page_size: 20,
        order_by: 'month',
        order_dir: 'asc',
        q: 'x',
      }),
    ).toMatchObject({
      page: 2,
      page_size: 20,
      order_by: 'month',
      order_dir: 'asc',
      search: 'x',
    })
  })

  it('parse: дефолты и фильтры; битый order_dir', () => {
    const empty = parseOfferListFromSearchParams(new URLSearchParams())
    expect(empty.order_by).toBe(OFFER_LIST_DEFAULT_ORDER_BY)
    expect(empty.order_dir).toBe(OFFER_LIST_DEFAULT_ORDER_DIR)

    const sp = new URLSearchParams(
      'q=a&direction_id=3&year=2024&month=5&order_by=amount&order_dir=asc',
    )
    expect(parseOfferListFromSearchParams(sp)).toMatchObject({
      q: 'a',
      direction_id: 3,
      year: 2024,
      month: 5,
      order_by: 'amount',
      order_dir: 'asc',
    })

    const bad = parseOfferListFromSearchParams(
      new URLSearchParams('direction_id=x&year=y&month=z&order_dir=side'),
    )
    expect(bad.direction_id).toBeUndefined()
    expect(bad.order_dir).toBe(OFFER_LIST_DEFAULT_ORDER_DIR)
  })
})
