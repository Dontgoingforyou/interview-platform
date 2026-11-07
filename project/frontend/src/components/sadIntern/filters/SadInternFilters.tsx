import { useState } from 'react'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import type { SelectOption } from '../../../types/common'
import type { SadInternListFilters } from '../../../types/sadIntern'
import { SAD_INTERN_STATUS_OPTIONS } from '../../../constants/sadInternStatuses'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

function deleteAllGroupPageParams(next: URLSearchParams): void {
  const keys = [...next.keys()].filter((k) => k.startsWith('page_'))
  for (const k of keys) {
    next.delete(k)
  }
}

interface SadInternFiltersProps {
  filters: SadInternListFilters
  directionOptions: SelectOption<number>[]
  directionsLoading: boolean
  searchParams: URLSearchParams
  setSearchParams: (next: URLSearchParams, opts?: { replace?: boolean }) => void
}

/** Фильтры списка «грустят». */
function SadInternFilters({
  filters,
  directionOptions,
  directionsLoading,
  searchParams,
  setSearchParams,
}: SadInternFiltersProps) {
  const [localQ, setLocalQ] = useState(filters.q ?? '')
  const [localStatus, setLocalStatus] = useState(filters.status ?? '')
  const [prevFilters, setPrevFilters] = useState(filters)
  if (prevFilters !== filters) {
    setPrevFilters(filters)
    setLocalQ(filters.q ?? '')
    setLocalStatus(filters.status ?? '')
  }

  const directionValue = directionOptions.find((o) => o.value === filters.direction) ?? null

  const applyToUrl = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('q')
        next.delete('status')
        next.delete('direction')
        deleteAllGroupPageParams(next)
        const q = localQ.trim()
        if (q) {
          next.set('q', q)
        }
        if (localStatus) {
          next.set('status', localStatus)
        }
        next.set('on_project_page', '1')
      }),
      { replace: true },
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    applyToUrl()
  }

  const onDirectionChange = (opt: SingleValue<SelectOption<number>>) => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('direction')
        deleteAllGroupPageParams(next)
        if (opt) {
          next.set('direction', String(opt.value))
        }
        next.set('on_project_page', '1')
      }),
      { replace: true },
    )
  }

  const reset = () => {
    setLocalQ('')
    setLocalStatus('')
    setSearchParams(new URLSearchParams(), { replace: true })
  }

  return (
    <ListPageFilterForm className="filter-form-wide" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="sad-intern-q">Поиск</label>
        <input
          id="sad-intern-q"
          type="search"
          value={localQ}
          onChange={(e) => setLocalQ(e.target.value)}
          placeholder="ФИО, Telegram, примечание…"
          className="form-input"
        />
      </div>
      <div className="filter-item">
        <label htmlFor="sad-intern-status">Статус</label>
        <select
          id="sad-intern-status"
          className="form-input"
          value={localStatus}
          onChange={(e) => setLocalStatus(e.target.value)}
        >
          <option value="">Все статусы</option>
          {SAD_INTERN_STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
      <div className="filter-item filter-item-select-wrap">
        <label htmlFor="sad-intern-direction">Направление</label>
        <Select<SelectOption<number>>
          inputId="sad-intern-direction"
          classNamePrefix="react-select"
          isLoading={directionsLoading}
          isClearable
          isSearchable
          menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
          menuPosition="fixed"
          placeholder="Все направления"
          options={directionOptions}
          value={directionValue}
          onChange={onDirectionChange}
          noOptionsMessage={() => 'Нет совпадений'}
        />
      </div>
      <div className="filter-buttons">
        <label className="filter-buttons-label-spacer">&nbsp;</label>
        <div className="button-group">
          <button type="submit">Применить</button>
          <button type="button" className="btn-secondary" onClick={reset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default SadInternFilters
