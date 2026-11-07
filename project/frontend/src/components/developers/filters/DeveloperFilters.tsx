import { useEffect, useMemo, useState } from 'react'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import type { SelectOption } from '../../../types/common'
import type { DeveloperListFilters } from '../../../types/developer'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

interface DeveloperFiltersProps {
  filters: DeveloperListFilters
  directionOptions: SelectOption<number>[]
  directionsLoading: boolean
  searchParams: URLSearchParams
  setSearchParams: (
    next: URLSearchParams,
    opts?: { replace?: boolean; preventScrollReset?: boolean },
  ) => void
}

/**
 * Фильтры списка разработчиков: поиск по ФИО, направление.
 */
function DeveloperFilters({
  filters,
  directionOptions,
  directionsLoading,
  searchParams,
  setSearchParams,
}: DeveloperFiltersProps) {
  const [localQ, setLocalQ] = useState(filters.q ?? '')
  const [localDirection, setLocalDirection] = useState<SelectOption<number> | null>(null)

  const directionFromFilters = useMemo((): SelectOption<number> | null => {
    if (filters.direction_id == null) {
      return null
    }
    return directionOptions.find((o) => o.value === filters.direction_id) ?? null
  }, [filters.direction_id, directionOptions])

  useEffect(() => {
    setLocalQ(filters.q ?? '')
  }, [filters.q])

  useEffect(() => {
    setLocalDirection(directionFromFilters)
  }, [directionFromFilters])

  const applyToUrl = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('q')
        next.delete('direction_id')
        next.delete('direction')
        const q = localQ.trim()
        if (q) {
          next.set('q', q)
        }
        if (localDirection) {
          next.set('direction_id', String(localDirection.value))
        }
        next.set('page', '1')
      }),
      { replace: true, preventScrollReset: true },
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    applyToUrl()
  }

  const handleReset = () => {
    setLocalQ('')
    setLocalDirection(null)
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('q')
        next.delete('direction_id')
        next.delete('direction')
        next.set('page', '1')
      }),
      { replace: true, preventScrollReset: true },
    )
  }

  const onDirectionSelectChange = (opt: SingleValue<SelectOption<number>>) => {
    setLocalDirection(opt)
  }

  return (
    <ListPageFilterForm aria-label="Фильтры разработчиков" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="developers-filter-q">Поиск</label>
        <input
          id="developers-filter-q"
          type="search"
          name="q"
          placeholder="ФИО…"
          value={localQ}
          onChange={(e) => setLocalQ(e.target.value)}
        />
      </div>

      <div className="filter-item filter-item-select-wrap">
        <label htmlFor="developers-filter-direction">Направление</label>
        <Select<SelectOption<number>>
          inputId="developers-filter-direction"
          classNamePrefix="react-select"
          isLoading={directionsLoading}
          isClearable
          isSearchable
          menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
          menuPosition="fixed"
          placeholder="Все направления"
          options={directionOptions}
          value={localDirection}
          onChange={onDirectionSelectChange}
          noOptionsMessage={() => 'Нет совпадений'}
        />
      </div>

      <div className="filter-buttons">
        <label htmlFor="developers-filter-submit" aria-hidden="true">
          &nbsp;
        </label>
        <div className="button-group">
          <button id="developers-filter-submit" type="submit" className="btn-primary">
            Применить
          </button>
          <button type="button" className="btn-secondary" onClick={handleReset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default DeveloperFilters
