import { describe, expect, it } from 'vitest'

import {
  directionMetricsFiltersKey,
  directionMetricsToApiParams,
  parseDirectionMetricsFromSearchParams,
} from '../../../utils/directions/directionMetricsParams'

describe('directionMetricsParams', () => {
  it('parse: пустой и заполненный query', () => {
    expect(parseDirectionMetricsFromSearchParams(new URLSearchParams())).toEqual({
      direction: null,
      min_conversion: null,
      date_filter: null,
    })
    const sp = new URLSearchParams('direction=4&min_conversion=0.2&date_filter=month')
    expect(parseDirectionMetricsFromSearchParams(sp)).toEqual({
      direction: 4,
      min_conversion: '0.2',
      date_filter: 'month',
    })
    expect(
      parseDirectionMetricsFromSearchParams(new URLSearchParams('direction=abc')),
    ).toEqual({ direction: null, min_conversion: null, date_filter: null })
  })

  it('toApiParams пропускает null', () => {
    expect(
      directionMetricsToApiParams({
        direction: 2,
        min_conversion: '0.1',
        date_filter: null,
      }),
    ).toEqual({ direction: '2', min_conversion: '0.1' })
  })

  it('filtersKey стабилен', () => {
    const key = directionMetricsFiltersKey({
      direction: 1,
      min_conversion: null,
      date_filter: 'week',
    })
    expect(JSON.parse(key)).toEqual({
      direction: 1,
      min_conversion: null,
      date_filter: 'week',
    })
  })
})
