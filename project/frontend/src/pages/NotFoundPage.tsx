import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div>
      <h1 className="page-title">Страница не найдена</h1>
      <p>
        <Link to="/interviews">На главную</Link>
      </p>
    </div>
  )
}

export default NotFoundPage
