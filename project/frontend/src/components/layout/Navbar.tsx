import { NavLink, useLocation } from 'react-router-dom'

import {
  NAV_ITEM_HELP,
  NAV_ITEMS_MAIN,
  sortNavItemsForHrOutstaff,
} from '../../constants/navigation'
import { useAuthStore } from '../../store/authStore'

function isHrOutstaffMenuRole(role: string): boolean {
  return role === 'hr' || role === 'outstaff'
}

function getVisibleMainItems(managerRole: string) {
  if (managerRole === 'mentor') {
    return NAV_ITEMS_MAIN.filter((i) => i.path === '/interviews-database')
  }
  if (isHrOutstaffMenuRole(managerRole)) {
    return sortNavItemsForHrOutstaff(NAV_ITEMS_MAIN.filter((i) => i.hrVisible))
  }
  return NAV_ITEMS_MAIN.filter((i) => {
    if (i.adminOnly && managerRole !== 'admin') {
      return false
    }
    return true
  })
}

/** Боковое меню: пункты по роли (manager / admin / HR / outstaff). */
function Navbar() {
  const managerRole = useAuthStore((s) => s.user?.manager_role ?? 'manager')
  const items = getVisibleMainItems(managerRole)
  const showHelp = managerRole === 'admin'
  const { pathname } = useLocation()

  return (
    <nav className="navbar" aria-label="Основное меню">
      <div className="navbar-container">
        <ul className="navbar-menu" id="navbarMenu">
          {items.map((item) => (
            <li key={item.path} className="navbar-item">
              <NavLink
                to={item.path}
                className={({ isActive }) => {
                  const active = isActive && !(item.excludePrefix && pathname.startsWith(item.excludePrefix))
                  return active ? 'navbar-link active' : 'navbar-link'
                }}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        {showHelp ? (
          <ul className="navbar-menu navbar-bottom">
            <li className="navbar-item">
              <NavLink
                to={NAV_ITEM_HELP.path}
                className={({ isActive }) =>
                  `navbar-link navbar-link--help${isActive ? ' active' : ''}`
                }
              >
                {NAV_ITEM_HELP.label}
              </NavLink>
            </li>
          </ul>
        ) : null}
      </div>
    </nav>
  )
}

export default Navbar
