import { useMemo, useState } from 'react'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import { MONTH_CHOICES } from '../../../constants/monthChoices'
import { useUrlParamSelect } from '../../../hooks/useUrlParamSelect'
import type { SelectOption } from '../../../types/common'
import type { OfferListFilters } from '../../../types/offer'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

const OFFER_FILTER_PARAM_KEYS = ['q', 'direction_id', 'year', 'month'] as const

interface OfferFiltersProps {
  filters: OfferListFilters
  directionOptions: SelectOption<number>[]
  directionsLoading: boolean
  searchParams: URLSearchParams
  setSearchParams: (next: URLSearchParams, opts?: { replace?: boolean }) => void
}

/**
 * Панель фильтров списка офферов.
 */
function OfferFilters({
  filters,
  directionOptions,
  directionsLoading,
  searchParams,
  setSearchParams,
}: OfferFiltersProps) {
  const [localQ, setLocalQ] = useState(filters.q ?? '')
  const [localYear, setLocalYear] = useState(filters.year != null ? String(filters.year) : '')
  const [localMonth, setLocalMonth] = useState(filters.month != null ? String(filters.month) : '')
  const [prevFilters, setPrevFilters] = useState(filters)
  if (prevFilters !== filters) {
    setPrevFilters(filters)
    setLocalQ(filters.q ?? '')
    setLocalYear(filters.year != null ? String(filters.year) : '')
    setLocalMonth(filters.month != null ? String(filters.month) : '')
  }

  const [directionFilter, setDirectionFilter] = useUrlParamSelect<number>(
    filters.direction_id != null ? String(filters.direction_id) : null,
    useMemo(
      () => (raw: string) => {
        const d = parseInt(raw, 10)
        if (Number.isNaN(d)) {
          return null
        }
        const found = directionOptions.find((o) => o.value === d)
        return { value: d, label: found ? found.label : `Направление #${d}` }
      },
      [directionOptions],
    ),
  )

  const applyToUrl = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        for (const k of OFFER_FILTER_PARAM_KEYS) {
          next.delete(k)
        }
        const q = localQ.trim()
        if (q) {
          next.set('q', q)
        }
        if (directionFilter?.value != null) {
          next.set('direction_id', String(directionFilter.value))
        }
        if (localYear.trim()) {
          next.set('year', localYear.trim())
        }
        if (localMonth) {
          next.set('month', localMonth)
        }
      }),
      { replace: true },
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    applyToUrl()
  }

  const handleReset = () => {
    setSearchParams(new URLSearchParams(), { replace: true })
  }

  return (
    <ListPageFilterForm aria-label="Фильтры офферов" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="offers-filter-q">Поиск</label>
        <input
          id="offers-filter-q"
          type="search"
          name="q"
          placeholder="ФИО, компания…"
          value={localQ}
          onChange={(e) => setLocalQ(e.target.value)}
        />
      </div>

      <div className="filter-item">
        <label htmlFor="offers-direction">Направление</label>
        <div className="filter-item-select-wrap">
          <Select<SelectOption<number>>
            inputId="offers-direction"
            classNamePrefix="react-select"
            placeholder="Начните вводить направление…"
            noOptionsMessage={() => 'Не найдено'}
            isClearable
            isSearchable
            menuPortalTarget={document.body}
            menuPosition="fixed"
            options={directionOptions}
            value={directionFilter}
            isLoading={directionsLoading}
            onChange={(opt: SingleValue<SelectOption<number>>) => setDirectionFilter(opt)}
          />
        </div>
      </div>

      <div className="filter-item">
        <label htmlFor="offers-year">Год</label>
        <input
          id="offers-year"
          type="number"
          name="year"
          placeholder="Например: 2025"
          value={localYear}
          onChange={(e) => setLocalYear(e.target.value)}
          min={2000}
          max={2100}
        />
      </div>

      <div className="filter-item">
        <label htmlFor="offers-month">Месяц</label>
        <select
          id="offers-month"
          value={localMonth}
          onChange={(e) => setLocalMonth(e.target.value)}
        >
          <option value="">Все</option>
          {MONTH_CHOICES.map((m) => (
            <option key={m.value} value={String(m.value)}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-buttons">
        <label htmlFor="offers-filter-submit"> </label>
        <div className="button-group" id="offers-filter-submit">
          <button type="submit">Применить</button>
          <button type="button" className="btn-secondary" onClick={handleReset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default OfferFilters
