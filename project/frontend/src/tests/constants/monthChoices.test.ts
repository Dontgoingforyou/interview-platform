import { describe, expect, it } from 'vitest'

import { MONTH_CHOICES, getMonthLabel } from '../../constants/monthChoices'

describe('monthChoices', () => {
  it('12 месяцев с value 1..12', () => {
    expect(MONTH_CHOICES).toHaveLength(12)
    expect(MONTH_CHOICES.map((m) => m.value)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  })

  it('getMonthLabel: известный и неизвестный месяц', () => {
    expect(getMonthLabel(3)).toBe('Март')
    expect(getMonthLabel(99)).toBe('99')
  })
})
