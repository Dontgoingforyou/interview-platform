import { describe, expect, it } from 'vitest'

import type { OfferAnalytics } from '../../../types/offer'
import {
  formatOfferMetricValue,
  numericOfferMetricValue,
} from '../../../utils/offers/offerMetricsDisplay'

describe('offerMetricsDisplay', () => {
  const raw = {
    total: 10,
    'avg-offer': 200000.7,
    'popular-company': 'Яндекс',
  } as OfferAnalytics

  it('numeric currency only', () => {
    expect(numericOfferMetricValue(raw, 'avg-offer', 'currency')).toBe(200000)
    expect(numericOfferMetricValue(raw, 'total')).toBeNull()
  })

  it('format currency / text / —', () => {
    expect(formatOfferMetricValue(raw, 'avg-offer', 'currency')).toContain('₽')
    expect(formatOfferMetricValue(raw, 'popular-company', 'text')).toBe('Яндекс')
    expect(formatOfferMetricValue({} as OfferAnalytics, 'x')).toBe('—')
  })
})
