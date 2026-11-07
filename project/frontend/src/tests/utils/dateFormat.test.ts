import { describe, expect, it } from 'vitest'

import { formatRuDate, formatShortRuDate } from '../../utils/dateFormat'

describe('formatRuDate', () => {
  it('DD.MM.YYYY / — / fallback', () => {
    expect(formatRuDate(null)).toBe('—')
    expect(formatRuDate(undefined)).toBe('—')
    expect(formatRuDate('2025-03-09T12:00:00Z')).toBe('09.03.2025')
    expect(formatRuDate('2025-03')).toBe('2025-03')
  })
})

describe('formatShortRuDate', () => {
  it('DD.MM.YY / — / raw fallback', () => {
    expect(formatShortRuDate(null)).toBe('—')
    expect(formatShortRuDate('  ')).toBe('—')
    expect(formatShortRuDate('2025-12-01')).toBe('01.12.25')
    expect(formatShortRuDate('01.12.2025')).toBe('01.12.2025')
  })
})
