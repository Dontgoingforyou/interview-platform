import { describe, expect, it } from 'vitest'

import {
  hasActiveListFilters,
  interviewTypeBadgeClass,
} from '../../../utils/interviews/interviewListUi'

describe('interviewTypeBadgeClass', () => {
  it.each([
    ['cancelled', 'interview-type-badge--danger'],
    ['final', 'interview-type-badge--success'],
    ['tech', 'interview-type-badge--tech'],
    ['tech_questionnaire', 'interview-type-badge--tech'],
    ['hr', 'interview-type-badge--hr'],
    ['screening', 'interview-type-badge--screening'],
    ['mock', 'interview-type-badge--muted'],
    ['test', 'interview-type-badge--muted'],
    ['other', 'interview-type-badge--default'],
  ] as const)('%s → %s', (type, cls) => {
    expect(interviewTypeBadgeClass(type)).toBe(cls)
  })
})

describe('hasActiveListFilters', () => {
  it('игнорирует page/order; видит фильтры', () => {
    expect(hasActiveListFilters(new URLSearchParams('page=2&order_by=date&order_dir=asc'))).toBe(
      false,
    )
    expect(hasActiveListFilters(new URLSearchParams('q=иван'))).toBe(true)
  })
})
