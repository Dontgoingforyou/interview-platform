import { useEffect, useId, useRef, useState } from 'react'

import { THEME_OPTIONS, type ThemeId, useThemeStore } from '../../store/themeStore'

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Кнопка переключения темы и выпадающий список вариантов. */
function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme)
  const setTheme = useThemeStore((s) => s.setTheme)
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)
  const btnRef = useRef<HTMLButtonElement>(null)
  const listId = useId()

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('click', onDocClick)
    return () => document.removeEventListener('click', onDocClick)
  }, [])

  const current = THEME_OPTIONS.find((o) => o.id === theme)
  const label = current?.label ?? 'Тема'
  const buttonIcon = current?.icon ?? '🌙'

  function pickTheme(next: ThemeId) {
    setOpen(false)
    setTheme(next)

    const btn = btnRef.current
    if (prefersReducedMotion()) {
      btn?.classList.remove('just-toggled')
      return
    }
    if (btn) {
      btn.classList.remove('just-toggled')
      void btn.offsetHeight
      btn.classList.add('just-toggled')
      window.setTimeout(() => btn.classList.remove('just-toggled'), 400)
    }
  }

  return (
    <div className="theme-toggle-wrap" ref={wrapRef}>
      <button
        ref={btnRef}
        type="button"
        className="theme-toggle-btn"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        title="Выбрать тему"
        onClick={(e) => {
          e.stopPropagation()
          setOpen((v) => !v)
        }}
      >
        {buttonIcon}
      </button>
      {open ? (
        <div className="theme-picker-dropdown" role="dialog" aria-label="Выбор темы" id={listId}>
          <ul className="theme-picker-list" role="listbox">
            {THEME_OPTIONS.map((opt) => (
              <li key={opt.id} role="none">
                <button
                  type="button"
                  role="option"
                  aria-selected={theme === opt.id}
                  className={`theme-picker-item${theme === opt.id ? ' is-selected' : ''}`}
                  onClick={() => pickTheme(opt.id)}
                >
                  <span className="theme-picker-icon" aria-hidden>
                    {opt.icon}
                  </span>
                  <span className="theme-picker-label">{opt.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <span className="visually-hidden">{label}</span>
    </div>
  )
}

export default ThemeToggle
