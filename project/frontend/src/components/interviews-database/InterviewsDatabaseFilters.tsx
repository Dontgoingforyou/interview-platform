import { useMemo, useId } from 'react'
import AsyncSelect from 'react-select/async'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import { getCompaniesFirstPage, searchCompanies, type CompanyOption, type DirectionOption } from '../../api/referenceApi'
import { INTERVIEW_TYPE_OPTIONS } from '../../constants/interviewTypes'
import { INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS } from '../../constants/interviewsDatabaseTranscriptionFilter'
import { useUrlParamSelect } from '../../hooks/useUrlParamSelect'
import ListPageFilterForm from '../ui/ListPageFilterForm'

type FilterChipItem = { id: string; label: string; paramKeys: string[] }

interface InterviewsDatabaseFiltersProps {
  searchParams: URLSearchParams
  directionsData: DirectionOption[]
  directionsLoading: boolean
  onUpdateParams: (updater: (p: URLSearchParams) => void) => void
  onReset: () => void
}

/** Фильтры страницы «База собеседований» (поиск, компания, направление, тип). */
export default function InterviewsDatabaseFilters({
  searchParams,
  directionsData,
  directionsLoading,
  onUpdateParams,
  onReset,
}: InterviewsDatabaseFiltersProps) {
  const chipsLabelId = useId()

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

  const typeParam = searchParams.get('interview_type')
  const [typeFilter, setTypeFilter] = useUrlParamSelect<string>(
    typeParam,
    useMemo(() => (raw) => {
      const found = INTERVIEW_TYPE_OPTIONS.find((o) => o.value === raw)
      return found ? { value: found.value, label: found.label } : { value: raw, label: raw }
    }, []),
  )

  const transcriptionParam = searchParams.get('transcription')
  const [transcriptionFilter, setTranscriptionFilter] = useUrlParamSelect<
    (typeof INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS)[number]['value']
  >(
    transcriptionParam,
    useMemo(
      () => (raw) => {
        const found = INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS.find((o) => o.value === raw)
        return found ? { value: found.value, label: found.label } : null
      },
      [],
    ),
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
      const qv = (fd.get('q') as string)?.trim()
      if (qv) {
        p.set('q', qv)
      } else {
        p.delete('q')
      }
      if (directionFilter?.value != null) {
        p.set('direction_id', String(directionFilter.value))
      } else {
        p.delete('direction_id')
      }
      if (companyFilter) {
        p.set('company', String(companyFilter.value))
      } else {
        p.delete('company')
      }
      if (typeFilter?.value) {
        p.set('interview_type', typeFilter.value)
      } else {
        p.delete('interview_type')
      }
      if (transcriptionFilter?.value) {
        p.set('transcription', transcriptionFilter.value)
      } else {
        p.delete('transcription')
      }
      p.set('page', '1')
    })
  }

  const handleReset = () => {
    setDirectionFilter(null)
    setCompanyFilter(null)
    setTypeFilter(null)
    setTranscriptionFilter(null)
    onReset()
  }

  const activeFilterChips = useMemo((): FilterChipItem[] => {
    const chips: FilterChipItem[] = []
    const q = searchParams.get('q')?.trim()
    if (q) {
      chips.push({ id: 'q', label: `Поиск: ${q}`, paramKeys: ['q'] })
    }
    if (directionFilter?.value != null) {
      chips.push({
        id: 'direction',
        label: `Направление: ${directionFilter.label}`,
        paramKeys: ['direction_id'],
      })
    }
    if (companyFilter?.value != null) {
      chips.push({
        id: 'company',
        label: `Компания: ${companyFilter.label}`,
        paramKeys: ['company'],
      })
    }
    const it = searchParams.get('interview_type')
    if (it) {
      const opt = INTERVIEW_TYPE_OPTIONS.find((o) => o.value === it)
      chips.push({
        id: 'itype',
        label: `Тип: ${opt?.label ?? it}`,
        paramKeys: ['interview_type'],
      })
    }
    const tr = searchParams.get('transcription')
    if (tr) {
      const opt = INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS.find((o) => o.value === tr)
      chips.push({
        id: 'transcription',
        label: `Транскрибация: ${opt?.label ?? tr}`,
        paramKeys: ['transcription'],
      })
    }
    return chips
  }, [searchParams, directionFilter, companyFilter])

  function removeFilterChip(paramKeys: string[]) {
    onUpdateParams((p) => {
      for (const k of paramKeys) {
        p.delete(k)
      }
      p.set('page', '1')
    })
    if (paramKeys.includes('direction_id')) {
      setDirectionFilter(null)
    }
    if (paramKeys.includes('company')) {
      setCompanyFilter(null)
    }
    if (paramKeys.includes('interview_type')) {
      setTypeFilter(null)
    }
    if (paramKeys.includes('transcription')) {
      setTranscriptionFilter(null)
    }
  }

  return (
    <ListPageFilterForm onSubmit={handleSubmit}>
      {activeFilterChips.length > 0 ? (
        <div className="interviews-filter-chips-wrap">
          <span className="interviews-filter-chips-label" id={chipsLabelId}>
            Активные фильтры
          </span>
          <div
            className="interviews-filter-chips"
            role="group"
            aria-labelledby={chipsLabelId}
          >
            {activeFilterChips.map((c) => (
              <button
                key={c.id}
                type="button"
                className="filter-chip"
                onClick={() => removeFilterChip(c.paramKeys)}
                aria-label={`Убрать фильтр: ${c.label}`}
              >
                <span className="filter-chip__text">{c.label}</span>
                <span className="filter-chip__remove" aria-hidden>
                  ×
                </span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="filter-item">
        <label htmlFor="idb-filter-q">Поиск</label>
        <input
          id="idb-filter-q"
          key={`idb-q-${searchParams.get('q') ?? ''}`}
          type="search"
          name="q"
          placeholder="ФИО, имя HR, ссылка на запись…"
          defaultValue={searchParams.get('q') ?? ''}
        />
      </div>

      <div className="filter-item">
        <label htmlFor="idb-filter-company">Компания</label>
        <div className="filter-item-select-wrap">
          <AsyncSelect
            inputId="idb-filter-company"
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
        <label htmlFor="idb-filter-direction">Направление</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="idb-filter-direction"
            classNamePrefix="react-select"
            placeholder="Все направления"
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
        <label htmlFor="idb-filter-type">Тип собеседования</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="idb-filter-type"
            classNamePrefix="react-select"
            placeholder="Все типы"
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

      <div className="filter-item">
        <label htmlFor="idb-filter-transcription">Транскрибация</label>
        <div className="filter-item-select-wrap">
          <Select
            inputId="idb-filter-transcription"
            classNamePrefix="react-select"
            placeholder="Все собеседования"
            noOptionsMessage={() => 'Нет вариантов'}
            isClearable
            isSearchable={false}
            options={INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER_OPTIONS}
            value={transcriptionFilter}
            onChange={(opt) => setTranscriptionFilter(opt)}
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
