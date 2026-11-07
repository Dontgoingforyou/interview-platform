import { describe, expect, it } from 'vitest'

import type { InterviewListFilters } from '../../types/interview'
import {
  buildInterviewListParams,
  parseInterviewListFromSearchParams,
} from '../../utils/interviews/interviewListParams'

describe('buildInterviewListParams', () => {
  it('возвращает пустой объект для пустых фильтров', () => {
    expect(buildInterviewListParams({})).toEqual({})
  })

  it('передаёт page и числовые id', () => {
    const filters: InterviewListFilters = {
      page: 2,
      direction_id: 3,
      company: 7,
    }
    expect(buildInterviewListParams(filters)).toEqual({
      page: 2,
      direction_id: 3,
      company: 7,
    })
  })

  it('передаёт строковые фильтры дат, поиска, сортировки и формата', () => {
    const filters: InterviewListFilters = {
      date_from: '2025-01-01',
      date_to: '2025-12-31',
      date_filter: 'week',
      q: 'иван',
      manager: 'boss@corp.ru',
      interview_type: 'tech',
      interview_format: 'online',
      order_by: 'date',
      order_dir: 'desc',
    }
    expect(buildInterviewListParams(filters)).toEqual({
      date_from: '2025-01-01',
      date_to: '2025-12-31',
      date_filter: 'week',
      q: 'иван',
      manager: 'boss@corp.ru',
      interview_type: 'tech',
      interview_format: 'online',
      order_by: 'date',
      order_dir: 'desc',
    })
  })

  it('передаёт has_video', () => {
    expect(buildInterviewListParams({ has_video: 'true' })).toEqual({ has_video: 'true' })
  })
})

describe('parseInterviewListFromSearchParams', () => {
  it('читает has_video из query', () => {
    const sp = new URLSearchParams('page=1&has_video=true')
    expect(parseInterviewListFromSearchParams(sp).has_video).toBe('true')
  })

  it('игнорирует невалидный has_video', () => {
    const sp = new URLSearchParams('has_video=maybe')
    expect(parseInterviewListFromSearchParams(sp).has_video).toBeUndefined()
  })
})
