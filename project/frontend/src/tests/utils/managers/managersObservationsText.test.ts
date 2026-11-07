import { describe, expect, it } from 'vitest'

import type {
  ManagersObservationListItem,
  ManagersObservations,
} from '../../../types/managerDashboard'
import { buildManagersObservationLines } from '../../../utils/managers/managersObservationsText'

function item(over: Partial<ManagersObservationListItem> = {}): ManagersObservationListItem {
  return {
    manager: 'Иван',
    candidates: 6,
    interviews: 25,
    successful: 3,
    upcoming: 2,
    cancelled: 1,
    week_count: 1,
    directions: 2,
    last_interview_date: null,
    hot_candidates: 1,
    active_candidates: 2,
    portfolio_candidates: 3,
    avgSpeed: 12,
    successRate: 0.55,
    ...over,
  }
}

describe('buildManagersObservationLines', () => {
  it('пусто при totalManagers=0', () => {
    const data: ManagersObservations = {
      list: [],
      totalManagers: 0,
      totalCandidates: 0,
      totalInterviews: 0,
      fastest: null,
      slowest: null,
      successSorted: [],
      busiest: null,
      biggestPortfolio: null,
      upcomingChamp: null,
      cancelledChamp: null,
      noSuccessYet: [],
    }
    expect(buildManagersObservationLines(data)).toEqual([])
  })

  it('инсайты с данными и fallback', () => {
    const rich: ManagersObservations = {
      list: [
        item(),
        item({
          manager: 'Пётр',
          candidates: 2,
          interviews: 5,
          successRate: 0.1,
          avgSpeed: null,
          upcoming: 0,
          week_count: 0,
          cancelled: 0,
        }),
      ],
      totalManagers: 2,
      totalCandidates: 8,
      totalInterviews: 30,
      fastest: item({ manager: 'Иван', avgSpeed: 10 }),
      slowest: item({ manager: 'Пётр', avgSpeed: 40 }),
      successSorted: [item({ manager: 'Иван', successRate: 0.55 }), item({ manager: 'Пётр', successRate: 0.1 })],
      busiest: item({ manager: 'Иван', interviews: 25 }),
      biggestPortfolio: item({ manager: 'Иван', candidates: 6 }),
      upcomingChamp: item({ manager: 'Иван', upcoming: 2 }),
      cancelledChamp: item({ manager: 'Иван', cancelled: 1 }),
      noSuccessYet: [item({ manager: 'Пётр' })],
    }
    const lines = buildManagersObservationLines(rich)
    expect(lines).toHaveLength(20)
    expect(lines[0]).toContain('2 менеджеров')
    expect(lines[2]).toContain('Иван')

    const sparse: ManagersObservations = {
      ...rich,
      fastest: null,
      slowest: null,
      successSorted: [],
      busiest: null,
      biggestPortfolio: null,
      upcomingChamp: null,
      cancelledChamp: null,
      noSuccessYet: [],
      totalInterviews: 0,
    }
    const fb = buildManagersObservationLines(sparse)
    expect(fb[2]).toContain('нет завершённых')
    expect(fb[4]).toContain('ещё нет')
  })
})
