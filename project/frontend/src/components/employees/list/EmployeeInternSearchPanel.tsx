import { Link } from 'react-router-dom'

import type { InternListItem } from '../../../types/intern'

interface EmployeeInternSearchPanelProps {
  searchValue: string
  onSearchChange: (value: string) => void
  debouncedQ: string
  isFetching: boolean
  isError: boolean
  isSuccess: boolean
  results: InternListItem[]
}

export default function EmployeeInternSearchPanel({
  searchValue,
  onSearchChange,
  debouncedQ,
  isFetching,
  isError,
  isSuccess,
  results,
}: EmployeeInternSearchPanelProps) {
  const searchPanelOpen =
    debouncedQ.length >= 2 && (isFetching || isError || isSuccess)

  return (
    <div className="search-container employee-search-container">
      <div className={`search-box${searchPanelOpen ? ' employee-search-box--has-panel' : ''}`}>
        <label htmlFor="employee-intern-search" className="visually-hidden">
          Поиск студента по имени
        </label>
        <input
          id="employee-intern-search"
          type="search"
          className="search-input"
          placeholder="Поиск студента по имени…"
          autoComplete="off"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        {debouncedQ.length >= 2 && isFetching ? (
          <div className="search-results search-results--loading">Поиск…</div>
        ) : null}
        {debouncedQ.length >= 2 && isError ? (
          <div className="search-results search-results--error">Ошибка поиска</div>
        ) : null}
        {debouncedQ.length >= 2 && isSuccess && results.length > 0 ? (
          <ul className="search-results employee-search-results" role="listbox">
            {results.map((row) => (
              <li key={row.id} role="option">
                {row.manager_email ? (
                  <Link
                    to={`/employees/${encodeURIComponent(row.manager_email)}`}
                    className="employee-search-hit"
                  >
                    <span className="employee-search-hit-name">{row.full_name}</span>
                    <span className="employee-search-hit-meta">
                      {row.group}
                      {row.manager_display_name ? ` · ${row.manager_display_name}` : ''}
                    </span>
                  </Link>
                ) : (
                  <span className="employee-search-hit employee-search-hit--disabled">
                    {row.full_name} (нет менеджера)
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : null}
        {debouncedQ.length >= 2 && isSuccess && results.length === 0 ? (
          <div className="search-results search-results--empty">Ничего не найдено</div>
        ) : null}
      </div>
    </div>
  )
}
