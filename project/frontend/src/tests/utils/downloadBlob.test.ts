import { afterEach, describe, expect, it, vi } from 'vitest'

import { downloadBlobResponse } from '../../utils/downloadBlob'

describe('downloadBlobResponse', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('создаёт ссылку с filename из Content-Disposition', () => {
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
    const click = vi.fn()
    const remove = vi.fn()
    const append = vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node)
    vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      rel: '',
      click,
      remove,
    } as unknown as HTMLAnchorElement)

    downloadBlobResponse(
      {
        data: new Blob(['x']),
        headers: { 'content-disposition': 'attachment; filename="report.csv"' },
      } as never,
      'fallback.bin',
    )

    expect(create).toHaveBeenCalled()
    expect(click).toHaveBeenCalled()
    expect(remove).toHaveBeenCalled()
    expect(revoke).toHaveBeenCalledWith('blob:mock')
    expect(append).toHaveBeenCalled()
  })

  it('использует fallback без Content-Disposition', () => {
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:x')
    const anchor = {
      href: '',
      download: '',
      rel: '',
      click: vi.fn(),
      remove: vi.fn(),
    }
    vi.spyOn(document, 'createElement').mockReturnValue(anchor as unknown as HTMLAnchorElement)
    vi.spyOn(document.body, 'appendChild').mockImplementation((n) => n)

    downloadBlobResponse({ data: new Blob(['y']), headers: {} } as never, 'out.xlsx')
    expect(anchor.download).toBe('out.xlsx')
  })
})
