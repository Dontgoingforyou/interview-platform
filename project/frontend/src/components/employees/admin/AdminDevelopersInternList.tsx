import { Link } from 'react-router-dom'

import type { AdminDeveloperRow } from '../../../types/employee'

interface AdminDevelopersInternListProps {
  interns: AdminDeveloperRow['interns']
}

export default function AdminDevelopersInternList({ interns }: AdminDevelopersInternListProps) {
  return (
    <div className="dev-list-inner">
      <ul className="dev-intern-list">
        {interns.map((intern) => (
          <li key={intern.id}>
            <Link
              to={`/interviews?q=${encodeURIComponent(intern.full_name)}`}
              className="dev-intern-name dev-intern-link"
            >
              {intern.full_name}
            </Link>
            {intern.group ? <span className="dev-intern-group">{intern.group}</span> : null}
          </li>
        ))}
      </ul>
    </div>
  )
}
