import { useEffect, useMemo, useState } from 'react'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import type { SelectOption } from '../../../types/common'
import type { DirectionMetricsPageFilters } from '../../../types/direction'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

const MIN_CONVERSION_OPTIONS: SelectOption<string>[] = [
  { value: '', label: 'Все' },
  { value: '0', label: '0% и выше' },
  { value: '25', label: '25% и выше' },
  { value: '50', label: '50% и выше' },
  { value: '75', label: '75% и выше' },
  { value: '100', label: '100%' },
]

interface DirectionMetricsFiltersProps {
  filters: DirectionMetricsPageFilters
  directionOptions: SelectOption<number>[]
  directionsLoading: boolean
  searchParams: URLSearchParams
  setSearchParams: (
    next: URLSearchParams,
    opts?: { replace?: boolean; preventScrollReset?: boolean },
  ) => void
}

/**
 * Фильтры метрик по направлениям: направление, мин. конверсия, дата анализа.
 */
function DirectionMetricsFilters({
  filters,
  directionOptions,
  directionsLoading,
  searchParams,
  setSearchParams,
}: DirectionMetricsFiltersProps) {
  const [localDirection, setLocalDirection] = useState<SelectOption<number> | null>(null)
  const [localMinConversion, setLocalMinConversion] = useState<SelectOption<string> | null>(
    MIN_CONVERSION_OPTIONS[0],
  )
  const [localDate, setLocalDate] = useState('')

  const directionFromFilters = useMemo((): SelectOption<number> | null => {
    if (filters.direction == null) {
      return null
    }
    return directionOptions.find((o) => o.value === filters.direction) ?? null
  }, [filters.direction, directionOptions])

  const minConvFromFilters = useMemo(() => {
    const v = filters.min_conversion
    if (v == null || v === '') {
      return MIN_CONVERSION_OPTIONS[0]
    }
    return MIN_CONVERSION_OPTIONS.find((o) => o.value === v) ?? MIN_CONVERSION_OPTIONS[0]
  }, [filters.min_conversion])

  useEffect(() => {
    setLocalDirection(directionFromFilters)
  }, [directionFromFilters])

  useEffect(() => {
    setLocalMinConversion(minConvFromFilters)
  }, [minConvFromFilters])

  useEffect(() => {
    setLocalDate(filters.date_filter ?? '')
  }, [filters.date_filter])

  const applyToUrl = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('direction')
        next.delete('min_conversion')
        next.delete('date_filter')
        if (localDirection) {
          next.set('direction', String(localDirection.value))
        }
        if (localMinConversion?.value) {
          next.set('min_conversion', localMinConversion.value)
        }
        if (localDate.trim()) {
          next.set('date_filter', localDate.trim())
        }
      }),
      { replace: true, preventScrollReset: true },
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    applyToUrl()
  }

  const handleReset = () => {
    setLocalDirection(null)
    setLocalMinConversion(MIN_CONVERSION_OPTIONS[0])
    setLocalDate('')
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.delete('direction')
        next.delete('min_conversion')
        next.delete('date_filter')
      }),
      { replace: true, preventScrollReset: true },
    )
  }

  const menuPortalTarget = typeof document !== 'undefined' ? document.body : null

  return (
    <ListPageFilterForm aria-label="Фильтры метрик по направлениям" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="direction-metrics-direction">Направление</label>
        <div className="filter-item-select-wrap">
          <Select<SelectOption<number>>
            inputId="direction-metrics-direction"
            classNamePrefix="react-select"
            placeholder="Все направления"
            isClearable
            isLoading={directionsLoading}
            options={directionOptions}
            value={localDirection}
            onChange={(opt: SingleValue<SelectOption<number>>) => setLocalDirection(opt)}
            menuPortalTarget={menuPortalTarget}
            menuPosition="fixed"
            styles={{ menuPortal: (base) => ({ ...base, zIndex: 10_000 }) }}
          />
        </div>
      </div>
      <div className="filter-item">
        <label htmlFor="direction-metrics-min-conv">Мин. конверсия (%)</label>
        <div className="filter-item-select-wrap">
          <Select<SelectOption<string>>
            inputId="direction-metrics-min-conv"
            classNamePrefix="react-select"
            placeholder="Все"
            isClearable={false}
            options={MIN_CONVERSION_OPTIONS}
            value={localMinConversion}
            onChange={(opt: SingleValue<SelectOption<string>>) =>
              setLocalMinConversion(opt ?? MIN_CONVERSION_OPTIONS[0])
            }
            menuPortalTarget={menuPortalTarget}
            menuPosition="fixed"
            styles={{ menuPortal: (base) => ({ ...base, zIndex: 10_000 }) }}
          />
        </div>
      </div>
      <div className="filter-item filter-item-date">
        <label htmlFor="direction-metrics-date">Дата для анализа</label>
        <input
          id="direction-metrics-date"
          type="date"
          name="date_filter"
          value={localDate}
          onChange={(e) => setLocalDate(e.target.value)}
        />
      </div>
      <div className="filter-buttons">
        <label htmlFor="direction-metrics-apply-wrap">&nbsp;</label>
        <div id="direction-metrics-apply-wrap" className="button-group">
          <button type="submit">Применить</button>
          <button type="button" className="btn-secondary" onClick={handleReset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default DirectionMetricsFilters
