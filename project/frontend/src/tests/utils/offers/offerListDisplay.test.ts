import { describe, expect, it } from 'vitest'

import { formatOfferAmountCell, offerTelegramHref } from '../../../utils/offers/offerListDisplay'

describe('offerTelegramHref', () => {
  it('null / @ / plain', () => {
    expect(offerTelegramHref(null)).toBeNull()
    expect(offerTelegramHref('  ')).toBeNull()
    expect(offerTelegramHref('@u')).toBe('https://t.me/u')
    expect(offerTelegramHref('u')).toBe('https://t.me/u')
  })
})

describe('formatOfferAmountCell', () => {
  it('форматирует число; — для пустого и NaN', () => {
    expect(formatOfferAmountCell(null)).toBe('—')
    expect(formatOfferAmountCell('')).toBe('—')
    expect(formatOfferAmountCell('abc')).toBe('—')
    expect(formatOfferAmountCell('150000.4')).toMatch(/150/)
  })
})
