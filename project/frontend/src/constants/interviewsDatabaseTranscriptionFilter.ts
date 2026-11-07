/** Значения query `transcription` для GET `/api/interviews-database/`. */
export const INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES = [
  'completed',
  'failed',
  'in_progress',
] as const

export type InterviewsDatabaseTranscriptionFilterValue =
  (typeof INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES)[number]

export const INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS: {
  value: InterviewsDatabaseTranscriptionFilterValue
  label: string
}[] = [
  { value: 'completed', label: 'Только транскрибированные' },
  { value: 'failed', label: 'С ошибкой транскрибации' },
  { value: 'in_progress', label: 'В процессе транскрибации' },
]

export function isInterviewsDatabaseTranscriptionFilterValue(
  raw: string,
): raw is InterviewsDatabaseTranscriptionFilterValue {
  return (INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_VALUES as readonly string[]).includes(raw)
}
