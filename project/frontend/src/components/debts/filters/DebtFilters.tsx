import { useState } from 'react'

import type { SelectOption } from '../../../types/common'
import type { DebtListFilters } from '../../../types/debt'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

const DEBT_FILTER_PARAM_KEYS = [
  'q',
  'direction',
  'payment_status',
  'not_paid_filter',
  'act_date_filter',
  'act_date_from',
  'act_date_to',
] as const

interface DebtFiltersProps {
  filters: DebtListFilters
  directionOptions: SelectOption<number>[]
  directionsLoading: boolean
  searchParams: URLSearchParams
  setSearchParams: (next: URLSearchParams, opts?: { replace?: boolean }) => void
}

/**
 * Панель фильтров списка долгов.
 */
function DebtFilters({
  filters,
  directionOptions,
  directionsLoading,
  searchParams,
  setSearchParams,
}: DebtFiltersProps) {
  const [localQ, setLocalQ] = useState(filters.q ?? '')
  const [localDirection, setLocalDirection] = useState(
    filters.direction != null ? String(filters.direction) : '',
  )
  const [localPaymentStatus, setLocalPaymentStatus] = useState(filters.payment_status ?? '')
  const [localNotPaid, setLocalNotPaid] = useState(filters.not_paid_filter ?? '')
  const [localActDateFilter, setLocalActDateFilter] = useState(filters.act_date_filter ?? '')
  const [localActDateFrom, setLocalActDateFrom] = useState(filters.act_date_from ?? '')
  const [localActDateTo, setLocalActDateTo] = useState(filters.act_date_to ?? '')
  const [prevFilters, setPrevFilters] = useState(filters)
  if (prevFilters !== filters) {
    setPrevFilters(filters)
    setLocalQ(filters.q ?? '')
    setLocalDirection(filters.direction != null ? String(filters.direction) : '')
    setLocalPaymentStatus(filters.payment_status ?? '')
    setLocalNotPaid(filters.not_paid_filter ?? '')
    setLocalActDateFilter(filters.act_date_filter ?? '')
    setLocalActDateFrom(filters.act_date_from ?? '')
    setLocalActDateTo(filters.act_date_to ?? '')
  }

  const applyToUrl = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        for (const k of DEBT_FILTER_PARAM_KEYS) {
          next.delete(k)
        }
        const q = localQ.trim()
        if (q) {
          next.set('q', q)
        }
        if (localDirection) {
          next.set('direction', localDirection)
        }
        if (localPaymentStatus) {
          next.set('payment_status', localPaymentStatus)
        }
        if (localNotPaid) {
          next.set('not_paid_filter', localNotPaid)
        }
        if (localActDateFilter) {
          next.set('act_date_filter', localActDateFilter)
        }
        if (localActDateFrom) {
          next.set('act_date_from', localActDateFrom)
        }
        if (localActDateTo) {
          next.set('act_date_to', localActDateTo)
        }
        next.set('page', '1')
      }),
      { replace: true },
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    applyToUrl()
  }

  return (
    <ListPageFilterForm aria-label="Фильтры долгов" onSubmit={handleSubmit}>
      <div className="filter-item">
        <label htmlFor="debts-filter-q">Поиск</label>
        <input
          id="debts-filter-q"
          type="search"
          name="q"
          placeholder="ФИО студента, телеграм, email…"
          value={localQ}
          onChange={(e) => setLocalQ(e.target.value)}
        />
      </div>

      <div className="filter-item">
        <label htmlFor="debts-direction">Направление</label>
        <select
          id="debts-direction"
          value={localDirection}
          disabled={directionsLoading}
          onChange={(e) => setLocalDirection(e.target.value)}
        >
          <option value="">Все</option>
          {directionOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-item">
        <label htmlFor="debts-payment-status">Статус</label>
        <select
          id="debts-payment-status"
          value={localPaymentStatus}
          onChange={(e) => setLocalPaymentStatus(e.target.value)}
        >
          <option value="">Все</option>
          <option value="searching">Снова ищем</option>
          <option value="paying">Платит</option>
          <option value="unknown">Без статуса</option>
        </select>
      </div>

      <div className="filter-item">
        <label htmlFor="debts-not-paid">Фильтр неплательщиков</label>
        <select
          id="debts-not-paid"
          value={localNotPaid}
          onChange={(e) => setLocalNotPaid(e.target.value)}
        >
          <option value="">Все</option>
          <option value="3months">Не платили 3 мес</option>
        </select>
      </div>

      <div className="filter-item filter-item-date">
        <span className="filter-item-date-label" id="debts-act-date-label">
          Фильтр по дате акта
        </span>
        <div className="date-row" role="group" aria-labelledby="debts-act-date-label">
          <select
            aria-label="Быстрый выбор даты акта"
            value={localActDateFilter}
            onChange={(e) => setLocalActDateFilter(e.target.value)}
          >
            <option value="">Быстрый выбор</option>
            <option value="today">Сегодня</option>
            <option value="this_month">Этот месяц</option>
          </select>
          <input
            type="date"
            aria-label="Дата акта с"
            value={localActDateFrom}
            onChange={(e) => setLocalActDateFrom(e.target.value)}
          />
          <input
            type="date"
            aria-label="Дата акта по"
            value={localActDateTo}
            onChange={(e) => setLocalActDateTo(e.target.value)}
          />
        </div>
      </div>

      <div className="filter-buttons">
        <label aria-hidden="true">&nbsp;</label>
        <div className="button-group">
          <button type="submit" className="btn-primary">
            Применить
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setSearchParams(new URLSearchParams(), { replace: true })
            }}
          >
            Сбросить
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default DebtFilters
