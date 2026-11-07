import { describe, expect, it } from 'vitest'

import {
  MANAGERS_CHART_MIN_PLOT_H,
  computeManagersInterviewsChartPlotHeight,
} from '../../../utils/managers/managersChartLayout'
import {
  managersRechartsTooltipContentStyle,
  managersRechartsTooltipCursor,
} from '../../../utils/managers/rechartsManagersTheme'

describe('computeManagersInterviewsChartPlotHeight', () => {
  it('не ниже минимума; растёт с числом строк до top N', () => {
    expect(computeManagersInterviewsChartPlotHeight(0)).toBe(MANAGERS_CHART_MIN_PLOT_H)
    expect(computeManagersInterviewsChartPlotHeight(2)).toBe(MANAGERS_CHART_MIN_PLOT_H)
    const tall = computeManagersInterviewsChartPlotHeight(20)
    expect(tall).toBeGreaterThan(MANAGERS_CHART_MIN_PLOT_H)
    expect(tall).toBe(computeManagersInterviewsChartPlotHeight(10))
  })
})

describe('rechartsManagersTheme', () => {
  it('экспортирует стили tooltip', () => {
    expect(managersRechartsTooltipCursor.fill).toContain('table-row-hover')
    expect(managersRechartsTooltipContentStyle.borderRadius).toBe(8)
  })
})
