import { afterEach, describe, expect, it, vi } from 'vitest'

import { prefersReducedMotion, runWithViewTransition } from '../../utils/viewTransition'

describe('viewTransition', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('prefersReducedMotion читает matchMedia', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })
    expect(prefersReducedMotion()).toBe(true)
  })

  it('runWithViewTransition: reduced motion → сразу updateDom', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      media: '',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })
    const update = vi.fn()
    runWithViewTransition(update)
    expect(update).toHaveBeenCalledOnce()
  })

  it('без API startViewTransition вызывает updateDom', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: false,
      media: '',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })
    const update = vi.fn()
    runWithViewTransition(update)
    expect(update).toHaveBeenCalledOnce()
  })

  it('с startViewTransition делегирует ему', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: false,
      media: '',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })
    const startViewTransition = vi.fn((cb: () => void) => {
      cb()
      return {} as ViewTransition
    })
    Object.defineProperty(document, 'startViewTransition', {
      configurable: true,
      value: startViewTransition,
    })
    const update = vi.fn()
    runWithViewTransition(update)
    expect(startViewTransition).toHaveBeenCalled()
    expect(update).toHaveBeenCalledOnce()
  })
})
