import { describe, expect, it } from 'vitest'

import { isYandexDiskPublicFileUrl } from '../../utils/yandexDiskUrl'

describe('isYandexDiskPublicFileUrl', () => {
  it.each([
    ['https://disk.yandex.ru/i/AbCdEf', true],
    ['https://yadi.sk/i/xyz', true],
    ['https://disk.360.yandex.ru/i/djK3RRsPTgaN3A', true],
    ['https://telemost.360.yandex.ru/j/9134424409', false],
    ['https://zoom.us/j/123', false],
    ['', false],
    ['https://disk.yandex.ru/client/disk', false],
  ] as const)('%s → %s', (url, expected) => {
    expect(isYandexDiskPublicFileUrl(url)).toBe(expected)
  })
})
