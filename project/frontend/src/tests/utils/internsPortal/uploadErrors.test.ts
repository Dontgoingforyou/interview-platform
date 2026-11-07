import { describe, expect, it } from 'vitest'

import {
  internPortalCeleryFailureMessage,
  internPortalUploadErrorMessage,
} from '../../../utils/internsPortal/uploadErrors'

describe('internPortalUploadErrorMessage', () => {
  it('возвращает текст сервера при 409', () => {
    const msg = internPortalUploadErrorMessage({
      response: { status: 409, data: { error: 'Уже идёт загрузка' } },
    })
    expect(msg).toBe('Уже идёт загрузка')
  })

  it('возвращает лимит при 429', () => {
    const msg = internPortalUploadErrorMessage({
      response: { status: 429, data: {} },
    })
    expect(msg).toContain('10 в час')
  })
})

describe('internPortalCeleryFailureMessage', () => {
  it('обрезает длинный статус FAILURE', () => {
    const long = 'x'.repeat(400)
    const msg = internPortalCeleryFailureMessage(long)
    expect(msg.length).toBeLessThanOrEqual(301)
    expect(msg.endsWith('…')).toBe(true)
  })
})
