import type { CSSProperties } from 'react'
import { Toaster } from 'sonner'

import { useThemeStore } from '../store/themeStore'

/**
 * Глобальные toast
 */
function AppToaster() {
  const themeId = useThemeStore((s) => s.theme)
  const theme = themeId === 'light' ? 'light' : 'dark'

  return (
    <Toaster
      theme={theme}
      position="top-right"
      richColors
      closeButton
      offset={{ top: '5rem', right: '1.5rem' }}
      mobileOffset={{ top: '4.5rem', right: '1rem', left: '1rem' }}
      style={
        {
          '--width': 'min(420px, calc(100vw - 3rem))',
        } as CSSProperties
      }
    />
  )
}

export default AppToaster
