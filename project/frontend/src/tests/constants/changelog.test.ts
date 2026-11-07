import { describe, expect, it } from 'vitest'

import {
  WHATS_NEW_ENTRIES,
  formatWhatsNewDate,
  hasUnseenWhatsNew,
  whatsNewPage,
  type WhatsNewEntry,
} from '../../constants/changelog'

function entry(version: string): WhatsNewEntry {
  return { version, date: '2026-10-22', text: `Текст ${version}` }
}

describe('hasUnseenWhatsNew', () => {
  it('не считает пустой журнал непрочитанным', () => {
    expect(hasUnseenWhatsNew(null, null)).toBe(false)
    expect(hasUnseenWhatsNew('1.1.323', null)).toBe(false)
    expect(hasUnseenWhatsNew(null, '')).toBe(false)
  })

  it('считает непрочитанным другой номер', () => {
    expect(hasUnseenWhatsNew(null, '1.1.324')).toBe(true)
    expect(hasUnseenWhatsNew('1.1.323', '1.1.324')).toBe(true)
    expect(hasUnseenWhatsNew('1.1.324', '1.1.324')).toBe(false)
  })
})

describe('whatsNewPage', () => {
  const entries = Array.from({ length: 11 }, (_, index) => entry(`1.1.${400 - index}`))

  it('отдаёт записи в заданном порядке порциями по 10', () => {
    const first = whatsNewPage(entries, 0)
    const second = whatsNewPage(entries, 1)
    expect(first).toHaveLength(10)
    expect(first[0]?.version).toBe('1.1.400')
    expect(first[9]?.version).toBe('1.1.391')
    expect(second).toEqual([entry('1.1.390')])
    expect(whatsNewPage(entries, -1)).toEqual([])
    expect(whatsNewPage(entries, 2)).toEqual([])
  })
})

describe('WHATS_NEW_ENTRIES', () => {
  it('содержит одну запись 1.0.1', () => {
    expect(WHATS_NEW_ENTRIES).toHaveLength(1)
    expect(WHATS_NEW_ENTRIES[0]?.version).toBe('1.0.1')
    expect(whatsNewPage(WHATS_NEW_ENTRIES, 0)).toHaveLength(1)
    expect(whatsNewPage(WHATS_NEW_ENTRIES, 1)).toHaveLength(0)
  })
})

describe('formatWhatsNewDate', () => {
  it('пишет день и месяц по-русски', () => {
    expect(formatWhatsNewDate('2026-03-21')).toBe('21 марта')
  })

  it('оставляет нераспознанную строку как есть', () => {
    expect(formatWhatsNewDate('21.03.2026')).toBe('21.03.2026')
  })
})
