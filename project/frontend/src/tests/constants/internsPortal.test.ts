import { describe, expect, it } from 'vitest'

import {
  INTERN_PORTAL_MAX_VIDEO_BYTES,
  INTERN_PORTAL_UPLOAD_TIMEOUT_MS,
  INTERN_PORTAL_VIDEO_ACCEPT,
} from '../../constants/internsPortal'

describe('internsPortal', () => {
  it('лимит видео 10 ГБ', () => {
    expect(INTERN_PORTAL_MAX_VIDEO_BYTES).toBe(10 * 1024 * 1024 * 1024)
  })

  it('accept содержит mp4 и timeout без лимита на клиенте', () => {
    expect(INTERN_PORTAL_VIDEO_ACCEPT).toContain('.mp4')
    expect(INTERN_PORTAL_UPLOAD_TIMEOUT_MS).toBe(0)
  })
})
