import type { CSSProperties, SVGProps } from 'react'

/** Подсветка области под курсором на графике (в духе hover строк таблицы) */
export const managersRechartsTooltipCursor: SVGProps<SVGElement> = {
  fill: 'var(--table-row-hover-bg)',
}

/** Общие стили Tooltip Recharts под тёмную/светлую тему приложения */
export const managersRechartsTooltipContentStyle: CSSProperties = {
  background: 'var(--card-bg, var(--bg-secondary))',
  border: '1px solid var(--border-color)',
  borderRadius: 8,
  fontSize: 13,
  color: 'var(--text-primary)',
}

export const managersRechartsTooltipLabelStyle: CSSProperties = {
  color: 'var(--text-secondary)',
  marginBottom: 4,
}

export const managersRechartsTooltipItemStyle: CSSProperties = {
  color: 'var(--text-primary)',
}

export const managersRechartsTooltipWrapperStyle: CSSProperties = {
  outline: 'none',
}
