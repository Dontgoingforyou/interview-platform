import { useState } from 'react'

import type { DebtByMonthFilters } from '../../../types/debt'
import { withClonedSearchParams } from '../../../utils/listPageSearchParams'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

interface DebtByMonthFiltersFormProps {
  filters: DebtByMonthFilters
  searchParams: URLSearchParams
  setSearchParams: (next: URLSearchParams, opts?: { replace?: boolean }) => void
}

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)

/** Фильтры периода для отчёта по месяцам. */
function DebtByMonthFiltersForm({
  filters,
  searchParams,
  setSearchParams,
}: DebtByMonthFiltersFormProps) {
  const [mf, setMf] = useState(filters.month_from ?? '')
  const [yf, setYf] = useState(filters.year_from ?? '')
  const [mt, setMt] = useState(filters.month_to ?? '')
  const [yt, setYt] = useState(filters.year_to ?? '')
  const [psf, setPsf] = useState(filters.payment_status_filter ?? '')
  const [prevFilters, setPrevFilters] = useState(filters)
  if (prevFilters !== filters) {
    setPrevFilters(filters)
    setMf(filters.month_from ?? '')
    setYf(filters.year_from ?? '')
    setMt(filters.month_to ?? '')
    setYt(filters.year_to ?? '')
    setPsf(filters.payment_status_filter ?? '')
  }

  const apply = () => {
    setSearchParams(
      withClonedSearchParams(searchParams, (next) => {
        next.set('page', '1')
        if (mf !== '' && mf != null) {
          next.set('month_from', String(mf))
        } else {
          next.delete('month_from')
        }
        if (yf !== '' && yf != null) {
          next.set('year_from', String(yf))
        } else {
          next.delete('year_from')
        }
        if (mt !== '' && mt != null) {
          next.set('month_to', String(mt))
        } else {
          next.delete('month_to')
        }
        if (yt !== '' && yt != null) {
          next.set('year_to', String(yt))
        } else {
          next.delete('year_to')
        }
        if (psf) {
          next.set('payment_status_filter', psf)
        } else {
          next.delete('payment_status_filter')
        }
      }),
      { replace: true },
    )
  }

  return (
    <ListPageFilterForm as="div" className="debt-by-month-filters">
      <div className="filter-item">
        <label id="debt-bm-from-label" htmlFor="debt-bm-month-from">
          С месяца
        </label>
        <div className="date-row" role="group" aria-labelledby="debt-bm-from-label">
          <select
            id="debt-bm-month-from"
            aria-label="Месяц с"
            value={mf === '' ? '' : String(mf)}
            onChange={(e) => setMf(e.target.value ? parseInt(e.target.value, 10) : '')}
          >
            <option value="">Месяц</option>
            {MONTH_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, '0')}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Год"
            min={2000}
            max={2100}
            aria-label="Год с"
            value={yf === '' ? '' : yf}
            onChange={(e) => setYf(e.target.value ? parseInt(e.target.value, 10) : '')}
          />
        </div>
      </div>
      <div className="filter-item">
        <label id="debt-bm-to-label" htmlFor="debt-bm-month-to">
          По месяц
        </label>
        <div className="date-row" role="group" aria-labelledby="debt-bm-to-label">
          <select
            id="debt-bm-month-to"
            aria-label="Месяц по"
            value={mt === '' ? '' : String(mt)}
            onChange={(e) => setMt(e.target.value ? parseInt(e.target.value, 10) : '')}
          >
            <option value="">Месяц</option>
            {MONTH_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, '0')}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Год"
            min={2000}
            max={2100}
            aria-label="Год по"
            value={yt === '' ? '' : yt}
            onChange={(e) => setYt(e.target.value ? parseInt(e.target.value, 10) : '')}
          />
        </div>
      </div>
      <div className="filter-item">
        <label htmlFor="debt-bm-payment-status">Статус оплаты</label>
        <select
          id="debt-bm-payment-status"
          value={psf}
          onChange={(e) => setPsf(e.target.value)}
        >
          <option value="">Все</option>
          <option value="paying">Платили</option>
          <option value="not_paying">Не платили</option>
          <option value="paid_fully">Полностью оплачено</option>
        </select>
      </div>
      <div className="filter-buttons">
        <label aria-hidden="true">&nbsp;</label>
        <div className="button-group">
          <button type="button" className="btn-primary" onClick={apply}>
            Применить
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setSearchParams(new URLSearchParams(), { replace: true })}
          >
            Сбросить все
          </button>
        </div>
      </div>
    </ListPageFilterForm>
  )
}

export default DebtByMonthFiltersForm
