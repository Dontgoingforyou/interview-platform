import type { FormEvent } from 'react'
import { useCallback } from 'react'
import type { SetURLSearchParams } from 'react-router-dom'

import type { CompanyListFilters as CompanyListFiltersState } from '../../../types/company'
import { COMPANY_LIST_META_KEYS } from '../../../utils/companies/companyListParams'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

type Props = {
  filters: CompanyListFiltersState
  searchParams: URLSearchParams
  setSearchParams: SetURLSearchParams
}

/**
 * Поиск по названию/псевдонимам и фильтр «бигтех».
 */
function CompanyFiltersBar({ filters, searchParams, setSearchParams }: Props) {
  const applySubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      const fd = new FormData(e.currentTarget)
      const q = String(fd.get('q') ?? '').trim()
      const bigtech = String(fd.get('bigtech') ?? '')
      setSearchParams(
        withClonedSearchParams(searchParams, (next) => {
          if (q) {
            next.set('q', q)
          } else {
            next.delete('q')
          }
          if (bigtech === '1' || bigtech === '0') {
            next.set('bigtech', bigtech)
          } else {
            next.delete('bigtech')
          }
          next.set('page', '1')
        }),
        { replace: true, preventScrollReset: true },
      )
    },
    [searchParams, setSearchParams],
  )

  const reset = useCallback(() => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        for (const k of [...next.keys()]) {
          if (COMPANY_LIST_META_KEYS.has(k)) {
            next.delete(k)
          }
        }
        next.set('sort', 'interviews')
      }),
      { replace: true, preventScrollReset: true },
    )
  }, [searchParams, setSearchParams])

  return (
    <ListPageFilterForm interviewsScoped={false} onSubmit={applySubmit}>
      <div className="filter-item">
        <label htmlFor="company-filter-q">Поиск</label>
        <input
          id="company-filter-q"
          name="q"
          type="search"
          defaultValue={filters.q}
          placeholder="Название или псевдоним…"
          autoComplete="off"
        />
      </div>
      <div className="filter-item">
        <label htmlFor="company-filter-bigtech">Тип</label>
        <select id="company-filter-bigtech" name="bigtech" defaultValue={filters.bigtech}>
          <option value="">Все компании</option>
          <option value="1">Бигтехи</option>
          <option value="0">Не бигтех</option>
        </select>
      </div>
      <div className="filter-buttons">
        <label className="filter-buttons-label" htmlFor="company-filter-submit">
          &nbsp;
        </label>
        <div className="button-group">
          <button id="company-filter-submit" type="submit">
            Применить
          </button>
          <button type="button" className="btn-link-reset" onClick={reset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default CompanyFiltersBar
