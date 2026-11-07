import { describe, expect, it } from 'vitest'

import type { InterviewAnalytics } from '../../../types/interview'
import {
  deepgramBalanceLabel,
  formatMetricValue,
  numericMetricValue,
} from '../../../utils/interviews/interviewMetricsDisplay'

describe('interviewMetricsDisplay gaps', () => {
  it('numeric null для отрицательных', () => {
    expect(numericMetricValue({ total: -1 } as InterviewAnalytics, 'total')).toBeNull()
  })

  it('format: — / percent / decimal2 / float / int', () => {
    expect(formatMetricValue({} as InterviewAnalytics, 'total')).toBe('—')
    expect(formatMetricValue({ rate: 12.34 } as never, 'rate', 'percent')).toBe('12.3%')
    expect(formatMetricValue({ avg: 1.2 } as never, 'avg', 'decimal2')).toBe('1.20')
    expect(formatMetricValue({ avg: 1.256 } as never, 'avg')).toBe('1.26')
    expect(formatMetricValue({ total: 5 } as InterviewAnalytics, 'total')).toBe('5')
  })

  it('deepgramBalanceLabel ветки', () => {
    expect(deepgramBalanceLabel(undefined, true)).toEqual({ text: 'Deepgram: …', isError: false })
    expect(deepgramBalanceLabel({ error: 'x' }, false)).toEqual({
      text: 'Deepgram: н/д',
      isError: true,
    })
    expect(deepgramBalanceLabel({ amount: 1.2 }, false)).toEqual({
      text: 'Deepgram: $1.20',
      isError: false,
    })
    expect(deepgramBalanceLabel({}, false)).toEqual({ text: 'Deepgram: —', isError: false })
  })
})
