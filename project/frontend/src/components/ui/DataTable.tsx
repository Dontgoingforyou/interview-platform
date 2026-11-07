import type { ReactNode } from 'react'

import TableScroll from './TableScroll'

interface DataTableProps {
  children: ReactNode
  /** Классы на `<table>`; по умолчанию `data-table`. */
  className?: string
  /** Доп. класс на обёртке `TableScroll`. */
  scrollClassName?: string
}

/**
 * Таблица списков: `TableScroll` + `table.data-table`.
 * Содержимое — `thead` / `tbody` с колонками фичи.
 */
function DataTable({ children, className = 'data-table', scrollClassName }: DataTableProps) {
  return (
    <TableScroll className={scrollClassName}>
      <table className={className}>{children}</table>
    </TableScroll>
  )
}

export default DataTable
