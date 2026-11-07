import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import AppToaster from './components/AppToaster.tsx'
import PersistGate from './components/PersistGate.tsx'
import './index.css'

// QueryClient — кэш и жизненный цикл запросов React Query.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

// createRoot монтирует приложение в #root (см. index.html).
createRoot(document.getElementById('root')!).render(
  // В dev StrictMode монтирует эффекты дважды — так проще ловить побочные эффекты.
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      {/* basename всегда '/' — приложение смонтировано в корне сайта.
          Vite base='/static/frontend/' нужен только для asset URL-ов, не для роутинга. */}
      <BrowserRouter basename="/">
        <PersistGate>
          <App />
          <AppToaster />
        </PersistGate>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
