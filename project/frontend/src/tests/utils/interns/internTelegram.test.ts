import { describe, expect, it } from 'vitest'

import { internTelegramHref } from '../../../utils/interns/internTelegram'

describe('internTelegramHref', () => {
  it('null / с @ / без @', () => {
    expect(internTelegramHref(null)).toBeNull()
    expect(internTelegramHref('@nick')).toBe('https://t.me/nick')
    expect(internTelegramHref('nick')).toBe('https://t.me/nick')
  })
})
