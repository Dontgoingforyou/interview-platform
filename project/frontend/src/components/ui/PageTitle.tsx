import type { ReactNode } from 'react'

interface PageTitleProps {
  children: ReactNode
}

/** Заголовок страницы верхнего уровня. */
function PageTitle({ children }: PageTitleProps) {
  return <h1 className="page-title">{children}</h1>
}

export default PageTitle
