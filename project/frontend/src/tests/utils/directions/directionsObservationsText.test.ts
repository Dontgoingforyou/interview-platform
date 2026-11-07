import { describe, expect, it } from 'vitest'

import type {
  DirectionObservationListItem,
  DirectionObservationsResponse,
} from '../../../types/direction'
import { buildDirectionObservationsLines } from '../../../utils/directions/directionsObservationsText'

function item(over: Partial<DirectionObservationListItem> = {}): DirectionObservationListItem {
  return {
    direction: 'Java',
    candidates: 25,
    interviews: 60,
    successful: 30,
    upcoming: 2,
    cancelled: 1,
    week_count: 1,
    managers: 3,
    last_interview_date: null,
    active_candidates: 5,
    avgSpeed: 10,
    successRate: 0.55,
    cancelRate: 0.05,
    ...over,
  }
}

describe('buildDirectionObservationsLines', () => {
  it('пустой список при totalDirections=0', () => {
    const data = {
      list: [],
      totalDirections: 0,
      totalCandidates: 0,
      totalInterviews: 0,
      fastest: null,
      slowest: null,
      highestCancel: null,
      mostManagers: null,
      highestUpcoming: null,
      bestConversion: null,
      worstConversion: null,
      focusNeeded: 0,
      bestMonth: null,
      worstMonth: null,
    } satisfies DirectionObservationsResponse
    expect(buildDirectionObservationsLines(data)).toEqual([])
  })

  it('формирует инсайты с данными и fallback-ветки', () => {
    const rich: DirectionObservationsResponse = {
      list: [
        item({ direction: 'Tech Backend', interviews: 60, successRate: 0.6, avgSpeed: 10 }),
        item({
          direction: 'QA',
          interviews: 3,
          candidates: 5,
          successRate: 0.1,
          avgSpeed: null,
          cancelRate: 0.2,
          upcoming: 0,
          managers: 1,
        }),
      ],
      totalDirections: 2,
      totalCandidates: 30,
      totalInterviews: 63,
      fastest: item({ direction: 'Java', avgSpeed: 8 }),
      slowest: item({ direction: 'QA', avgSpeed: 40 }),
      highestCancel: item({ direction: 'QA', cancelRate: 0.2 }),
      mostManagers: item({ direction: 'Java', managers: 5 }),
      highestUpcoming: item({ direction: 'Java', upcoming: 4 }),
      bestConversion: item({ direction: 'Java', successRate: 0.6 }),
      worstConversion: item({ direction: 'QA', successRate: 0.1 }),
      focusNeeded: 1,
      bestMonth: ['Январь', 20],
      worstMonth: ['Июль', 2],
    }
    const lines = buildDirectionObservationsLines(rich)
    expect(lines).toHaveLength(20)
    expect(lines[0]).toContain('2 направлений')
    expect(lines[1]).toContain('Java')
    expect(lines[9]).toContain('Январь')

    const sparse: DirectionObservationsResponse = {
      ...rich,
      fastest: null,
      slowest: null,
      highestCancel: null,
      mostManagers: null,
      highestUpcoming: null,
      bestConversion: null,
      worstConversion: null,
      bestMonth: null,
      worstMonth: null,
      list: [item({ direction: 'Other', interviews: 1, successRate: 0, avgSpeed: null })],
    }
    const fallback = buildDirectionObservationsLines(sparse)
    expect(fallback[1]).toContain('мало данных')
    expect(fallback[3]).toContain('не измерима')
    expect(fallback[9]).toContain('равномерно')
  })
})
