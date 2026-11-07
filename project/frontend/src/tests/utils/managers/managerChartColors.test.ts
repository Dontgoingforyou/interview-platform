import { afterEach, describe, expect, it, vi } from 'vitest'

import { readManagerChartColors } from '../../../utils/managers/managerChartColors'

describe('readManagerChartColors', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('читает CSS-переменные из document', () => {
    vi.spyOn(window, 'getComputedStyle').mockReturnValue({
      getPropertyValue: (name: string) => {
        if (name === '--accent-red') return ' #ff0000 '
        if (name === '--accent-green') return ' #00ff00 '
        if (name === '--accent-primary') return ' #0000ff '
        return ''
      },
    } as CSSStyleDeclaration)

    expect(readManagerChartColors()).toEqual({
      hot: '#ff0000',
      active: '#0000ff',
      portfolio: '#00ff00',
      primary: '#0000ff',
    })
  })

  it('fallback при пустых переменных', () => {
    vi.spyOn(window, 'getComputedStyle').mockReturnValue({
      getPropertyValue: () => '',
    } as unknown as CSSStyleDeclaration)

    const c = readManagerChartColors()
    expect(c.hot).toBe('#f85149')
    expect(c.portfolio).toBe('#3fb950')
  })
})
