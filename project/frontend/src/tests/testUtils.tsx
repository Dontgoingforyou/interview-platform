/* eslint-disable react-refresh/only-export-components -- утилиты и обёртки для Vitest, не hot-reload */
/**
 * Обёртки для тестов компонентов: React Query без повторных попыток, MemoryRouter с basename SPA.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

/** Как в main.tsx / vite base — пути в MemoryRouter без префикса ведут сюда. */
export const TEST_BASENAME = ''

/** QueryClient для юнит-тестов: без retry, детерминированные ошибки. */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

export interface TestProvidersProps {
  children: ReactNode
  queryClient?: QueryClient
  /**
   * Полные пути в истории (как в адресной строке браузера), с префиксом basename.
   * Пример: `/interviews` при корневом basename.
   */
  initialEntries?: string[]
}

export function TestProviders({
  children,
  queryClient = createTestQueryClient(),
  initialEntries = ['/interviews'],
}: TestProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter basename={TEST_BASENAME} initialEntries={initialEntries}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

export interface RenderWithProvidersOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient
  initialEntries?: string[]
}

/** render + QueryClientProvider + MemoryRouter. */
export function renderWithProviders(
  ui: ReactElement,
  {
    queryClient,
    initialEntries,
    ...renderOptions
  }: RenderWithProvidersOptions = {},
) {
  const client = queryClient ?? createTestQueryClient()
  return render(ui, {
    wrapper: ({ children }) => (
      <TestProviders queryClient={client} initialEntries={initialEntries}>
        {children}
      </TestProviders>
    ),
    ...renderOptions,
  })
}
