import type { ReactNode } from 'react'

interface PageHeaderActionsProps {
  children: ReactNode
}

/** Правая панель кнопок над фильтром / таблицей. */
function PageHeaderActions({ children }: PageHeaderActionsProps) {
  return (
    <div className="page-header-with-actions">
      <div className="page-header-buttons">{children}</div>
    </div>
  )
}

export default PageHeaderActions
