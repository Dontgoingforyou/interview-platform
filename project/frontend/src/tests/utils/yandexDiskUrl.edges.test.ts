import { describe, expect, it } from 'vitest'

import { isYandexDiskPublicFileUrl } from '../../utils/yandexDiskUrl'

describe('isYandexDiskPublicFileUrl edges', () => {
  it('отклоняет без схемы, битый URL, пустой path, showcaptcha', () => {
    expect(isYandexDiskPublicFileUrl(null)).toBe(false)
    expect(isYandexDiskPublicFileUrl('ftp://disk.yandex.ru/i/x')).toBe(false)
    expect(isYandexDiskPublicFileUrl('https://disk.yandex.ru/')).toBe(false)
    expect(isYandexDiskPublicFileUrl('https://disk.yandex.ru/showcaptcha/x')).toBe(false)
    expect(isYandexDiskPublicFileUrl('https://%')).toBe(false)
    expect(isYandexDiskPublicFileUrl('https://foo.disk.yandex.ru/d/abc')).toBe(true)
  })
})
