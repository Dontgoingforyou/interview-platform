import { NavLink } from 'react-router-dom'

/** Навигация портала стажёра. */
function NavbarStudent() {
  return (
    <nav className="navbar" aria-label="Меню портала стажёра">
      <div className="navbar-container">
        <ul className="navbar-menu" id="navbarMenu">
          <li className="navbar-item">
            <NavLink to="/interns-portal" className={({ isActive }) => (isActive ? 'navbar-link active' : 'navbar-link')}>
              Мои собеседования
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  )
}

export default NavbarStudent
