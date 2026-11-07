import { useEffect, useRef } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { isDevBypassAuth } from '../../constants/devAuth'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import {
  useMarkStudentInternalLinkClicks,
  useStudentLogoutOnTabClose,
} from '../../hooks/useStudentLogoutOnTabClose'
import { useAuthStore } from '../../store/authStore'
import { isPureStudentPortalUser } from '../../utils/authRoles'
import { useUiStore } from '../../store/uiStore'
import ChangelogButton from './ChangelogButton'
import ThemeToggle from './ThemeToggle'
import WeatherEffect from './WeatherEffect'
import Navbar from './Navbar'
import NavbarStudent from './NavbarStudent'

function MainLayout() {
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)

  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useUiStore((s) => s.toggleSidebar)
  const mobileMenuOpen = useUiStore((s) => s.mobileMenuOpen)
  const setMobileMenuOpen = useUiStore((s) => s.setMobileMenuOpen)
  const toggleMobileMenu = useUiStore((s) => s.toggleMobileMenu)

  const location = useLocation()
  const contentContainerRef = useRef<HTMLDivElement>(null)
  const isMobile = useMediaQuery('(max-width: 768px)')
  const pureStudentPortal = isPureStudentPortalUser(user)

  useStudentLogoutOnTabClose(pureStudentPortal)
  useMarkStudentInternalLinkClicks(pureStudentPortal)

  useEffect(() => {
    document.documentElement.classList.remove('sidebar-collapsed-initial')
  }, [])

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname, setMobileMenuOpen])

  useEffect(() => {
    const el = contentContainerRef.current
    if (!el) {
      return
    }
    const run = () => {
      el.focus({ preventScroll: true })
    }
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(run)
    } else {
      run()
    }
  }, [location.pathname])

  useEffect(() => {
    if (!isMobile) {
      setMobileMenuOpen(false)
    }
  }, [isMobile, setMobileMenuOpen])

  function handleLogout() {
    clearSession()
    if (isDevBypassAuth()) {
      window.location.assign('/login')
      return
    }
    window.location.href = '/accounts/logout/'
  }

  const isInternPortalRoute = location.pathname === '/interns-portal'
  const pageClass = [
    'page-wrapper',
    sidebarCollapsed && !isMobile ? 'sidebar-collapsed' : '',
    isInternPortalRoute ? 'intern-portal-page' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const sidebarClass = `sidebar${mobileMenuOpen && isMobile ? ' active' : ''}`

  return (
    <>
      <WeatherEffect />
      <div className={pageClass}>
      <div className="shell-corner">
        <ChangelogButton />
        <ThemeToggle />
      </div>

      {!isMobile ? (
        <button
          type="button"
          className="sidebar-collapse-btn"
          onClick={toggleSidebar}
          aria-label="Скрыть или показать навигацию"
          title="Скрыть/показать навигацию"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      ) : null}

      {isMobile ? (
        <button
          type="button"
          className={`navbar-toggle${mobileMenuOpen ? ' active' : ''}`}
          id="navbarToggle"
          onClick={toggleMobileMenu}
          aria-label="Открыть меню"
          aria-expanded={mobileMenuOpen}
        >
          <span />
          <span />
          <span />
        </button>
      ) : null}

      {isMobile && mobileMenuOpen ? (
        <button
          type="button"
          className="layout-backdrop"
          aria-label="Закрыть меню"
          onClick={() => setMobileMenuOpen(false)}
        />
      ) : null}

      <aside className={sidebarClass}>
        <header className="sidebar-header">
          <h1 className="main-title">Платформа собеседований</h1>
          {user ? (
            <div className="user-info">
              <span>Привет, {user.full_name}!</span>
              <button type="button" className="btn-logout" onClick={handleLogout}>
                Выйти
              </button>
            </div>
          ) : null}
        </header>
        {pureStudentPortal ? <NavbarStudent /> : <Navbar />}
      </aside>

      <main className="main-content">
        <div
          ref={contentContainerRef}
          className="content-container"
          tabIndex={-1}
          role="region"
          aria-label="Содержимое страницы"
        >
          <Outlet />
        </div>
      </main>
    </div>
    </>
  )
}

export default MainLayout
