/**
 * Цвета графиков из CSS-переменных темы.
 */
export interface ManagerChartColors {
  hot: string
  active: string
  portfolio: string
  primary: string
}

export function readManagerChartColors(): ManagerChartColors {
  if (typeof document === 'undefined') {
    return {
      hot: '#f85149',
      active: '#58a6ff',
      portfolio: '#3fb950',
      primary: '#58a6ff',
    }
  }
  const s = getComputedStyle(document.documentElement)
  const hot = s.getPropertyValue('--accent-red').trim()
  const portfolio = s.getPropertyValue('--accent-green').trim()
  const primary = s.getPropertyValue('--accent-primary').trim()
  return {
    hot: hot || '#f85149',
    active: primary || '#58a6ff',
    portfolio: portfolio || '#3fb950',
    primary: primary || '#58a6ff',
  }
}
