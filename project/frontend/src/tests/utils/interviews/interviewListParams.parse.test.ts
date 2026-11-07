import { describe, expect, it } from 'vitest'

import { parseInterviewListFromSearchParams } from '../../../utils/interviews/interviewListParams'

describe('parseInterviewListFromSearchParams coverage', () => {
  it('читает основные фильтры списка', () => {
    const sp = new URLSearchParams(
      'page=3&q=иван&manager=m@x.ru&direction_id=4&company=7&interview_type=tech&interview_format=online&date_from=2025-01-01&date_to=2025-02-01&date_filter=week&order_by=date&order_dir=asc&has_video=false',
    )
    expect(parseInterviewListFromSearchParams(sp)).toMatchObject({
      page: 3,
      q: 'иван',
      manager: 'm@x.ru',
      direction_id: 4,
      company: 7,
      interview_type: 'tech',
      interview_format: 'online',
      date_from: '2025-01-01',
      date_to: '2025-02-01',
      date_filter: 'week',
      order_by: 'date',
      order_dir: 'asc',
      has_video: 'false',
    })
  })

  it('игнорирует битые числа и order_dir', () => {
    const f = parseInterviewListFromSearchParams(
      new URLSearchParams('page=0&direction_id=x&company=y&order_dir=side'),
    )
    expect(f.page).toBe(1)
    expect(f.direction_id).toBeUndefined()
    expect(f.company).toBeUndefined()
    expect(f.order_dir).toBeUndefined()
  })
})
