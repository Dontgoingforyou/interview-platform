import { useMemo } from 'react'
import AsyncSelect from 'react-select/async'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import { getCompaniesFirstPage, searchCompanies, type CompanyOption, type DirectionOption, type ManagerFilterOption } from '../../api/referenceApi'
import { INTERVIEW_FORMAT_OPTIONS, INTERVIEW_TYPE_OPTIONS } from '../../constants/interviewTypes'
import { useUrlParamSelect } from '../../hooks/useUrlParamSelect'
import ListPageFilterForm from '../ui/ListPageFilterForm'

const DATE_FILTER_LABELS: Record<string, string> = {
  today: 'Сегодня',
  tomorrow: 'Завтра',
}

const DATE_QUICK_FILTER_OPTIONS = [
  { value: 'today', label: DATE_FILTER_LABELS.today },
  { value: 'tomorrow', label: DATE_FILTER_LABELS.tomorrow },
]

interface InterviewFiltersProps {
  searchParams: URLSearchParams
  managersData: ManagerFilterOption[]
  managersLoading: boolean
  directionsData: DirectionOption[]
  directionsLoading: boolean
  onUpdateParams: (updater: (p: URLSearchParams) => void) => void
  onReset: () => void
}

export default function InterviewFilters({
  searchParams,
  managersData,
  managersLoading,
  directionsData,
  directionsLoading,
  onUpdateParams,
  onReset,
}: InterviewFiltersProps) {
  const companyParam = searchParams.get('company')
  const [companyFilter, setCompanyFilter] = useUrlParamSelect<number>(
    companyParam,
    useMemo(() => (raw) => {
      const c = parseInt(raw, 10)
      if (Number.isNaN(c)) {
        return null
      }
      return { value: c, label: `Компания #${c}` }
    }, []),
  )

  const managerParam = searchParams.get('manager')
  const [managerFilter, setManagerFilter] = useUrlParamSelect<string>(
    managerParam,
    useMemo(() => (raw) => {
      const found = managersData.find((x) => x.email === raw)
      return { value: raw, label: found ? found.full_name : raw }
    }, [managersData]),
  )

  const directionParam = searchParams.get('direction_id')
  const [directionFilter, setDirectionFilter] = useUrlParamSelect<number>(
    directionParam,
    useMemo(() => (raw) => {
      const d = parseInt(raw, 10)
      if (Number.isNaN(d)) {
        return null
      }
      const found = directionsData.find((x) => x.id === d)
      return { value: d, label: found ? found.name : `Направление #${d}` }
    }, [directionsData]),
  )

  const formatParam = searchParams.get('interview_format')
  const [formatFilter, setFormatFilter] = useUrlParamSelect<string>(
    formatParam,
    useMemo(() => (raw) => {
      const found = INTERVIEW_FORMAT_OPTIONS.find((o) => o.value === raw)
      return found ? { value: found.value, label: found.label } : { value: raw, label: raw }
    }, []),
  )

  const typeParam = searchParams.get('interview_type')
  const [typeFilter, setTypeFilter] = useUrlParamSelect<string>(
    typeParam,
    useMemo(() => (raw) => {
      const found = INTERVIEW_TYPE_OPTIONS.find((o) => o.value === raw)
      return found ? { value: found.value, label: found.label } : { value: raw, label: raw }
    }, []),
  )

  const dateFilterParam = searchParams.get('date_filter')
  const [dateQuickFilter, setDateQuickFilter] = useUrlParamSelect<string>(
    dateFilterParam,
    useMemo(() => (raw) => {
      if (raw !== 'today' && raw !== 'tomorrow') {
        return null
      }
      return { value: raw, label: DATE_FILTER_LABELS[raw] ?? raw }
    }, []),
  )

  const loadCompanyOptions = useMemo(
    () => async (inputValue: string) => {
      const list = inputValue.trim() ? await searchCompanies(inputValue) : await getCompaniesFirstPage()
      return list.map((co: CompanyOption) => ({ value: co.id, label: co.name }))
    },
    [],
  )

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    onUpdateParams((p) => {
      p.delete('no_link')
      p.delete('intern_id')
      const hasVideo = (fd.get('has_video') as string) || ''
      if (hasVideo === 'true' || hasVideo === 'false') {
        p.set('has_video', hasVideo)
      } else {
        p.delete('has_video')
      }
      const qv = (fd.get('q') as string)?.trim()
      if (qv) {
        p.set('q', qv)
      } else {
        p.delete('q')
      }
      if (managerFilter?.value) {
        p.set('manager', managerFilter.value)
      } else {
        p.delete('manager')
      }
      if (directionFilter?.value) {
        p.set('direction_id', String(directionFilter.value))
      } else {
        p.delete('direction_id')
      }
      if (companyFilter) {
        p.set('company', String(companyFilter.value))
      } else {
        p.delete('company')
      }
      if (formatFilter?.value) {
        p.set('interview_format', formatFilter.value)
      } else {
        p.delete('interview_format')
      }
      const df = fd.get('date_from') as string
      if (df) {
        p.set('date_from', df)
      } else {
        p.delete('date_from')
      }
      const dt = fd.get('date_to') as string
      if (dt) {
        p.set('date_to', dt)
      } else {
        p.delete('date_to')
      }
      if (dateQuickFilter?.value) {
        p.set('date_filter', dateQuickFilter.value)
      } else {
        p.delete('date_filter')
      }
      if (typeFilter?.value) {
        p.set('interview_type', typeFilter.value)
      } else {
        p.delete('interview_type')
      }
      p.set('page', '1')
    })
  }

  const handleReset = () => {
    setManagerFilter(null)
    setDirectionFilter(null)
    setCompanyFilter(null)
    setFormatFilter(null)
    setTypeFilter(null)
    setDateQuickFilter(null)
    onReset()
  }

  return (
    <ListPageFilterForm onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="interview-filter-q">Поиск</label>
        <input
          id="interview-filter-q"
          key={`interview-q-${searchParams.get('q') ?? ''}`}
          type="search"
          name="q"
          placeholder="ФИО, HR, ссылка..."
          defaultValue={searchParams.get('q') ?? ''}
        />
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-manager">Менеджер</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interview-filter-manager"
            classNamePrefix="react-select"
            placeholder="Начните вводить имя…"
            noOptionsMessage={() => 'Не найдено'}
            isClearable
            isSearchable
            isLoading={managersLoading}
            options={managersData.map((m) => ({ value: m.email, label: m.full_name }))}
            value={managerFilter}
            onChange={(opt) => setManagerFilter(opt)}
            menuPortalTarget={document.body}
            menuPosition="fixed"
          />
        </div>
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-direction">Направление</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interview-filter-direction"
            classNamePrefix="react-select"
            placeholder="Начните вводить напр…"
            noOptionsMessage={() => 'Не найдено'}
            isClearable
            isSearchable
            isLoading={directionsLoading}
            options={directionsData.map((d) => ({ value: d.id, label: d.name }))}
            value={directionFilter}
            onChange={(opt) => setDirectionFilter(opt)}
            menuPortalTarget={document.body}
            menuPosition="fixed"
          />
        </div>
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-company">Компания</label>
        <div className="filter-item-select-wrap">
          <AsyncSelect
            inputId="interview-filter-company"
            classNamePrefix="react-select"
            placeholder="Начните вводить компанию…"
            cacheOptions
            defaultOptions
            isClearable
            loadOptions={loadCompanyOptions}
            value={companyFilter}
            onChange={(opt) => setCompanyFilter(opt)}
            menuPortalTarget={document.body}
            menuPosition="fixed"
          />
        </div>
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-format">Формат</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interview-filter-format"
            classNamePrefix="react-select"
            placeholder="Все"
            noOptionsMessage={() => 'Нет вариантов'}
            isClearable
            isSearchable={false}
            options={INTERVIEW_FORMAT_OPTIONS}
            value={formatFilter}
            onChange={(opt: SingleValue<{ value: string; label: string }>) => setFormatFilter(opt)}
            menuPortalTarget={document.body}
            menuPosition="fixed"
          />
        </div>
      </div>

      <div className="filter-item filter-item-date">
        <span className="filter-item-date-label" id="interview-date-filter-label">
          Фильтр по дате
        </span>
        <div className="date-row" aria-labelledby="interview-date-filter-label">
          <div className="filter-item-select-wrap">
            <Select
              inputId="interview-date-filter-quick"
              classNamePrefix="react-select"
              placeholder="Быстрый выбор"
              noOptionsMessage={() => 'Нет вариантов'}
              isClearable
              isSearchable={false}
              options={DATE_QUICK_FILTER_OPTIONS}
              value={dateQuickFilter}
              onChange={(opt: SingleValue<{ value: string; label: string }>) => setDateQuickFilter(opt)}
              menuPortalTarget={document.body}
              menuPosition="fixed"
            />
          </div>
          <input
            type="date"
            name="date_from"
            key={`interview-df-${searchParams.get('date_from') ?? ''}`}
            defaultValue={searchParams.get('date_from') ?? ''}
            aria-label="Дата с"
          />
          <input
            type="date"
            name="date_to"
            key={`interview-dt-${searchParams.get('date_to') ?? ''}`}
            defaultValue={searchParams.get('date_to') ?? ''}
            aria-label="Дата по"
          />
        </div>
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-has-video">Запись (видео)</label>
        <select
          id="interview-filter-has-video"
          name="has_video"
          key={`interview-hv-${searchParams.get('has_video') ?? ''}`}
          defaultValue={searchParams.get('has_video') ?? ''}
        >
          <option value="">Все</option>
          <option value="true">С загруженной записью</option>
          <option value="false">Без записи</option>
        </select>
      </div>

      <div className="filter-item">
        <label htmlFor="interview-filter-type">Тип</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="interview-filter-type"
            classNamePrefix="react-select"
            placeholder="Все"
            noOptionsMessage={() => 'Нет вариантов'}
            isClearable
            isSearchable={false}
            options={INTERVIEW_TYPE_OPTIONS}
            value={typeFilter}
            onChange={(opt: SingleValue<{ value: string; label: string }>) => setTypeFilter(opt)}
            menuPortalTarget={document.body}
            menuPosition="fixed"
          />
        </div>
      </div>

      <div className="filter-buttons">
        <label aria-hidden="true">&nbsp;</label>
        <div className="button-group">
          <button type="submit">Применить</button>
          <button type="button" onClick={handleReset}>
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}
