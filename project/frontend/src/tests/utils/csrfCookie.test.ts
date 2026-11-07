import { afterEach, describe, expect, it } from 'vitest'

import { getCookie } from '../../utils/csrfCookie'

describe('getCookie', () => {
  afterEach(() => {
    document.cookie = 'csrftoken=; Max-Age=0; path=/'
    document.cookie = 'other=; Max-Age=0; path=/'
  })

  it('читает значение cookie', () => {
    document.cookie = 'csrftoken=abc%20123; path=/'
    expect(getCookie('csrftoken')).toBe('abc 123')
  })

  it('null если нет cookie', () => {
    expect(getCookie('missing_token')).toBeNull()
  })
})
