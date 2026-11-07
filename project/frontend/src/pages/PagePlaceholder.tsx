import PageTitle from '../components/ui/PageTitle'

interface PagePlaceholderProps {
  title: string
}

/** Заглушка раздела («в разработке»). */
function PagePlaceholder({ title }: PagePlaceholderProps) {
  return (
    <div>
      <PageTitle>{title}</PageTitle>
      <p className="page-intro">Раздел в разработке.</p>
    </div>
  )
}

export default PagePlaceholder
