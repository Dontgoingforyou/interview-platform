/**
 * Общая инициализация для Vitest (матчеры Testing Library для expect()).
 */
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Vitest не всегда очищает DOM между тестами так же, как Jest + RTL по умолчанию.
afterEach(() => {
  cleanup()
})

// jsdom не реализует matchMedia — нужен для useMediaQuery в компонентах (MetricsGridSection и др.).
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// MetricAnimatedStrong и др. — анимация при появлении в viewport.
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null
  readonly rootMargin = ''
  readonly thresholds: readonly number[] = []
  disconnect() {}
  observe() {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
  unobserve() {}
}
globalThis.IntersectionObserver =
  MockIntersectionObserver as unknown as typeof IntersectionObserver

// TableScroll — jsdom не предоставляет ResizeObserver.
class MockResizeObserver implements ResizeObserver {
  private readonly cb: ResizeObserverCallback

  constructor(cb: ResizeObserverCallback) {
    this.cb = cb
  }

  disconnect() {}
  observe() {
    queueMicrotask(() => {
      this.cb([], this)
    })
  }
  unobserve() {}
}
globalThis.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver
