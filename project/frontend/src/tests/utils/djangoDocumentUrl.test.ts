import { describe, expect, it } from 'vitest'

import { getDjangoDocumentUrl } from '../../utils/djangoDocumentUrl'

describe('getDjangoDocumentUrl', () => {
  it('нормализует путь со слэшем', () => {
    const url = getDjangoDocumentUrl('debts/export/')
    expect(url === '/debts/export/' || url.endsWith('/debts/export/')).toBe(true)
  })

  it('оставляет абсолютный path', () => {
    const url = getDjangoDocumentUrl('/help/')
    expect(url.endsWith('/help/')).toBe(true)
  })
})
