import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import {
  INTERN_STATUS_FILTER_OPTIONS,
} from '../../constants/internStatuses'
import { useUrlParamSelect } from '../../hooks/useUrlParamSelect'
import ListPageFilterForm from '../ui/ListPageFilterForm'
import type { InternListFilters } from '../../types/intern'

interface InternFiltersProps {
  filters: InternListFilters
  managerOptions: { value: string; label: string }[]
  directionOptions: { value: number; label: string }[]
  managersLoading: boolean
  directionsLoading: boolean
  onUpdateParams: (mut: (p: URLSearchParams) => void) => void
}

function InternFilters({
  filters,
  managerOptions,
  directionOptions,
  managersLoading,
  directionsLoading,
  onUpdateParams,
}: InternFiltersProps) {
  const navigate = useNavigate()

  /** Локальное состояние селектов — URL обновляется только по кнопке «Применить». */
  const [managerFilter, setManagerFilter] = useUrlParamSelect<string>(
    filters.manager ?? null,
    useMemo(
      () => (raw) => {
        const found = managerOptions.find((o) => o.value === raw)
        return { value: raw, label: found ? found.label : raw }
      },
      [managerOptions],
    ),
  )

  const [directionFilter, setDirectionFilter] = useUrlParamSelect<number>(
    filters.direction_id != null ? String(filters.direction_id) : null,
    useMemo(
      () => (raw) => {
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

  const [statusFilter, setStatusFilter] = useUrlParamSelect<string>(
    filters.status ?? null,
    useMemo(
      () => (raw) => {
        const found = INTERN_STATUS_FILTER_OPTIONS.find((o) => o.value === raw)
        return found ? { value: found.value, label: found.label } : { value: raw, label: raw }
      },
      [],
    ),
  )

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    onUpdateParams((next) => {
      const q = String(fd.get('q') ?? '').trim()
      if (q) {
        next.set('q', q)
      } else {
        next.delete('q')
      }
      if (managerFilter?.value) {
        next.set('manager', managerFilter.value)
      } else {
        next.delete('manager')
      }
      if (directionFilter?.value != null) {
        next.set('direction_id', String(directionFilter.value))
      } else {
        next.delete('direction_id')
      }
      if (statusFilter?.value) {
        next.set('status', statusFilter.value)
      } else {
        next.delete('status')
      }
      next.set('page', '1')
    })
  }

  return (
    <ListPageFilterForm aria-label="Фильтры студентов" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="interns-q">Поиск</label>
        <input
          id="interns-q"
          name="q"
          placeholder="ФИО, email, группа, HR…"
          defaultValue={filters.q ?? ''}
        />
      </div>
      <div className="filter-item">
        <label htmlFor="interns-manager">Менеджер</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interns-manager"
            classNamePrefix="react-select"
            placeholder="Начните вводить менеджера…"
            noOptionsMessage={() => 'Не найдено'}
            isClearable
            isSearchable
            menuPortalTarget={document.body}
            menuPosition="fixed"
            options={managerOptions}
            value={managerFilter}
            isLoading={managersLoading}
            onChange={(opt: SingleValue<{ value: string; label: string }>) => setManagerFilter(opt)}
          />
        </div>
      </div>
      <div className="filter-item">
        <label htmlFor="interns-direction">Направление</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interns-direction"
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
            onChange={(opt: SingleValue<{ value: number; label: string }>) =>
              setDirectionFilter(opt)
            }
          />
        </div>
      </div>
      <div className="filter-item">
        <label htmlFor="interns-status">Статус</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interns-status"
            classNamePrefix="react-select"
            placeholder="Все"
            options={INTERN_STATUS_FILTER_OPTIONS}
            value={statusFilter}
            isSearchable={false}
            isClearable
            menuPortalTarget={document.body}
            menuPosition="fixed"
            onChange={(opt: SingleValue<{ value: string; label: string }>) => setStatusFilter(opt)}
          />
        </div>
      </div>
      <div className="filter-buttons">
        <label aria-hidden="true">&nbsp;</label>
        <div className="button-group">
          <button type="submit">Применить</button>
          <button type="button" onClick={() => navigate('/interns')}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default InternFilters
