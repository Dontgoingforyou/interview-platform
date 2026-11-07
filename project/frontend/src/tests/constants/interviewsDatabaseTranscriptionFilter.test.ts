import { describe, expect, it } from 'vitest'

import {
  INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS,
  INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES,
  isInterviewsDatabaseTranscriptionFilterValue,
} from '../../constants/interviewsDatabaseTranscriptionFilter'

describe('interviewsDatabaseTranscriptionFilter', () => {
  it('принимает известные значения', () => {
    for (const v of INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES) {
      expect(isInterviewsDatabaseTranscriptionFilterValue(v)).toBe(true)
    }
  })

  it('отклоняет неизвестное', () => {
    expect(isInterviewsDatabaseTranscriptionFilterValue('pending')).toBe(false)
    expect(isInterviewsDatabaseTranscriptionFilterValue('')).toBe(false)
  })

  it('опции покрывают все значения', () => {
    expect(INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS.map((o) => o.value)).toEqual([
      ...INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES,
    ])
  })
})
