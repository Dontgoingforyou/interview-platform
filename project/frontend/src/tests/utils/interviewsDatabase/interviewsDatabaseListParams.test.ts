import { describe, expect, it } from 'vitest'

import {
  buildInterviewsDatabaseListParams,
  parseInterviewsDatabaseListFromSearchParams,
} from '../../../utils/interviewsDatabase/interviewsDatabaseListParams'

describe('buildInterviewsDatabaseListParams', () => {
  it('пустой и полный', () => {
    expect(buildInterviewsDatabaseListParams({})).toEqual({})
    expect(
      buildInterviewsDatabaseListParams({
        page: 2,
        q: 'x',
        company: 3,
        direction_id: 4,
        interview_type: 'tech',
        transcription: 'completed',
        order_by: 'date',
        order_dir: 'asc',
      }),
    ).toEqual({
      page: 2,
      q: 'x',
      company: 3,
      direction_id: 4,
      interview_type: 'tech',
      transcription: 'completed',
      order_by: 'date',
      order_dir: 'asc',
    })
  })
})

describe('parseInterviewsDatabaseListFromSearchParams', () => {
  it('читает валидные поля; отбрасывает невалидный transcription', () => {
    const sp = new URLSearchParams(
      'page=2&q=a&company=5&direction_id=6&interview_type=hr&transcription=completed&order_by=date&order_dir=desc',
    )
    expect(parseInterviewsDatabaseListFromSearchParams(sp)).toMatchObject({
      page: 2,
      q: 'a',
      company: 5,
      direction_id: 6,
      interview_type: 'hr',
      transcription: 'completed',
      order_by: 'date',
      order_dir: 'desc',
    })

    const bad = parseInterviewsDatabaseListFromSearchParams(
      new URLSearchParams('page=x&company=y&transcription=pending&order_dir=side'),
    )
    expect(bad.page).toBe(1)
    expect(bad.company).toBeUndefined()
    expect(bad.transcription).toBeUndefined()
    expect(bad.order_dir).toBeUndefined()
  })
})
