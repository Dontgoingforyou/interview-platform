import type { ReactNode } from 'react'

interface PageIntroCardProps {
  title: string
  children?: ReactNode
}

/** Карточка с заголовком и вводным текстом вверху раздела. */
function PageIntroCard({ title, children }: PageIntroCardProps) {
  return (
    <section className="page-intro-card">
      <h1>{title}</h1>
      {children}
    </section>
  )
}

export default PageIntroCard
