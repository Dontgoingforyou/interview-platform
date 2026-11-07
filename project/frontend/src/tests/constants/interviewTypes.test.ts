import { describe, expect, it } from 'vitest'

import { INTERVIEW_FORMAT_OPTIONS, INTERVIEW_TYPE_OPTIONS } from '../../constants/interviewTypes'

describe('interviewTypes', () => {
  it('типы содержат screening и cancelled', () => {
    const values = INTERVIEW_TYPE_OPTIONS.map((o) => o.value)
    expect(values).toContain('screening')
    expect(values).toContain('cancelled')
  })

  it('форматы: online/office/phone', () => {
    expect(INTERVIEW_FORMAT_OPTIONS.map((o) => o.value)).toEqual(['online', 'office', 'phone'])
  })
})
