import { useCallback, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import Pagination from '../../components/Pagination'
import DebtByMonthFiltersForm from '../../components/debts/filters/DebtByMonthFiltersForm'
import DebtByMonthDesktopTable from '../../components/debts/list/DebtByMonthDesktopTable'
import DebtByMonthMobileCards from '../../components/debts/list/DebtByMonthMobileCards'
import { CollapsibleSection, InlineError, PageIntroCard } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import { useDebtsByMonth } from '../../hooks/debts/useDebtsByMonth'
import { parseDebtByMonthFromSearchParams } from '../../utils/debts/debtByMonthParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { withClonedSearchParams } from '../../utils/listPageSearchParams'
function extractErrorDetail(err: unknown): string | null {
  const ax = err as { response?: { data?: { detail?: string } } }
  const d = ax.response?.data?.detail
  return typeof d === 'string' ? d : null
}

/**
 * Просмотр долгов и платежей за выбранный период месяцев.
 */
function DebtsByMonthPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseDebtByMonthFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const filtersPanelId = useId()

  const { query, exportMonths, selectedPeriod, count, totalPages, currentPage, results, hasPeriod } =
    useDebtsByMonth(filters)

  const updateParams = useCallback(
    (mut: (next: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut), { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const errMsg = query.isError ? extractErrorDetail(query.error) : null

  return (
    <div className="page debts-list-page">
      <PageIntroCard title={`Данные по долгам за период: ${hasPeriod ? selectedPeriod : 'не выбран'}`} />

      <p className="debts-by-month-back">
        <Link to="/debts" className="btn-secondary">
          Назад к списку долгов
        </Link>
      </p>

      <CollapsibleSection
        sectionId={filtersPanelId}
        expanded={filtersExpanded}
        onExpandedChange={setFiltersExpanded}
        title="Поиск и фильтры"
        headingId="debts-by-month-filters-heading"
      >
        <DebtByMonthFiltersForm
          filters={filters}
          searchParams={searchParams}
          setSearchParams={setSearchParams}
        />
      </CollapsibleSection>

      {query.isFetching && query.data ? <LoadingLine message="Загрузка…" /> : null}

      {query.isError ? (
        <InlineError
          message={errMsg ?? 'Не удалось загрузить отчёт. Проверьте период и попробуйте снова.'}
        />
      ) : null}

      {hasPeriod && query.isSuccess ? (
        <section
          className={withListDataRefreshingClass(
            'debts-by-month-results',
            isListBackgroundRefetch(query.isFetching, Boolean(query.data)),
          )}
        >
          <p className="filter-results-summary interns-filter-summary">
            Записей: <strong>{count}</strong>
          </p>
          {results.length === 0 ? (
            <p className="empty-state-msg" role="status">
              Нет данных за выбранный период.
            </p>
          ) : (
            <>
              <DebtByMonthDesktopTable results={results} exportMonths={exportMonths} />
              <DebtByMonthMobileCards results={results} exportMonths={exportMonths} />
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={(p) => {
                  updateParams((next) => {
                    next.set('page', String(p))
                  })
                }}
                showPageInput
              />
            </>
          )}
        </section>
      ) : null}

      {!hasPeriod ? (
        <p className="muted">Укажите начальный и конечный месяц/год и нажмите «Применить».</p>
      ) : null}
    </div>
  )
}

export default DebtsByMonthPage
