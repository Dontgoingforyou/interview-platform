import { describe, expect, it } from 'vitest'

import { safeExternalUrl } from '../../utils/safeExternalUrl'

describe('safeExternalUrl', () => {
  it('null для пустого и опасных схем', () => {
    expect(safeExternalUrl(null)).toBeNull()
    expect(safeExternalUrl('')).toBeNull()
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('data:text/html,hi')).toBeNull()
    expect(safeExternalUrl('//evil.example')).toBeNull()
  })

  it('пропускает http/https', () => {
    expect(safeExternalUrl('https://example.com/a')).toBe('https://example.com/a')
    expect(safeExternalUrl('http://example.com')).toContain('http://example.com')
  })

  it('отклоняет не-http протоколы', () => {
    expect(safeExternalUrl('ftp://files.example/x')).toBeNull()
  })
})
