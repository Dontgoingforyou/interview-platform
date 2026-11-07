import { useCallback, useId, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { postDebtImport } from '../../api/debtsApi'
import { getDirections } from '../../api/referenceApi'
import DebtMetricsMainGrid from '../../components/debts/analytics/DebtMetricsMainGrid'
import DebtFilters from '../../components/debts/filters/DebtFilters'
import DebtListDesktopTable from '../../components/debts/list/DebtListDesktopTable'
import DebtListEmptyState from '../../components/debts/list/DebtListEmptyState'
import DebtListMobileCards from '../../components/debts/list/DebtListMobileCards'
import DebtListSkeleton from '../../components/debts/list/DebtListSkeleton'
import DebtListTableHead from '../../components/debts/list/DebtListTableHead'
import Pagination from '../../components/Pagination'
import {
  CollapsibleSection,
  ImportModal,
  InlineError,
  LoadingLine,
  PageHeaderActions,
  PageIntroCard,
} from '../../components/ui'
import { useAsyncFileImport } from '../../hooks/useAsyncFileImport'
import { useDebtsList } from '../../hooks/debts/useDebtsList'
import { useMeaningfulListFilters } from '../../hooks/useMeaningfulListFilters'
import { useAuthStore } from '../../store/authStore'
import { parseDebtListFromSearchParams } from '../../utils/debts/debtListParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { applyTableSortToSearchParams, withClonedSearchParams } from '../../utils/listPageSearchParams'

/**
 * Список долгов: метрики, фильтры, таблица.
 */
function DebtsListPage() {
  const user = useAuthStore((s) => s.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseDebtListFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const filtersPanelId = useId()
  const importModalTitleId = useId()

  const debtImport = useAsyncFileImport(postDebtImport, [['debts']])
  const hasActiveSemanticFilters = useMeaningfulListFilters(searchParams)

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const {
    analyticsQuery,
    listQuery,
    deleteMutation,
    count,
    totalPages,
    currentPage,
    results,
    lastFourMonthLabels,
    isAdmin,
  } = useDebtsList(filters, user)

  const directionOptions = useMemo(
    () =>
      (directionsQuery.data ?? []).map((d) => ({
        value: d.id,
        label: d.name,
      })),
    [directionsQuery.data],
  )

  const updateParams = useCallback(
    (mut: (next: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut), { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      updateParams((next) => {
        applyTableSortToSearchParams(next, field, 'desc')
        next.set('page', '1')
      })
    },
    [updateParams],
  )

  const isInitialLoad =
    (analyticsQuery.isLoading && !analyticsQuery.data) || (listQuery.isLoading && !listQuery.data)

  const skeletonHead = (
    <DebtListTableHead
      filters={filters}
      onToggleSort={toggleSort}
      lastFourMonthLabels={[]}
      isAdmin={isAdmin}
    />
  )

  return (
    <div className="page debts-list-page">
      <PageIntroCard title="Аналитика долгов отдела">
        <p>
          Все записи из таблицы «Долги» с расчётом прогресса выплат, остатка и динамики по месяцам.
          Используйте фильтры и поиск, чтобы быстро найти человека, направление или проблемную ситуацию.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <DebtListSkeleton tableHead={skeletonHead} />
      ) : (
        <div key="page-ready" className="interns-page-ready">
          {analyticsQuery.isError ? (
            <InlineError message="Не удалось загрузить аналитику долгов." />
          ) : null}
          {analyticsQuery.data ? <DebtMetricsMainGrid analytics={analyticsQuery.data} /> : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="debts-filters-heading"
          >
            <DebtFilters
              filters={filters}
              directionOptions={directionOptions}
              directionsLoading={directionsQuery.isLoading}
              searchParams={searchParams}
              setSearchParams={setSearchParams}
            />
          </CollapsibleSection>

          {listQuery.isFetching && listQuery.data ? (
            <LoadingLine message="Обновление списка…" />
          ) : null}
          {listQuery.isError ? (
            <InlineError message="Не удалось загрузить долги. Попробуйте обновить страницу." />
          ) : null}

          {hasActiveSemanticFilters && listQuery.data ? (
            <p className="filter-results-summary interns-filter-summary">
              Найдено записей: <strong>{count}</strong>
            </p>
          ) : null}

          {isAdmin ? (
            <div className="interviews-subsection">
              <PageHeaderActions>
                <Link className="btn-success" to="/debts/new">
                  + Новые данные о долгах
                </Link>
                <button type="button" className="btn-primary" onClick={() => setImportOpen(true)}>
                  Импортировать таблицу
                </button>
                <Link className="btn-secondary" to="/debts/by-month">
                  Просмотр по месяцам
                </Link>
              </PageHeaderActions>
            </div>
          ) : null}

          {!listQuery.isLoading && !listQuery.isError ? (
            <section
              className={withListDataRefreshingClass(
                'interns-list-section',
                isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
              )}
            >
              {results.length === 0 ? (
                <DebtListEmptyState />
              ) : (
                <>
                  <DebtListDesktopTable
                    filters={filters}
                    onToggleSort={toggleSort}
                    results={results}
                    lastFourMonthLabels={lastFourMonthLabels}
                    isAdmin={isAdmin}
                    onDeleteDebt={(id) => deleteMutation.mutate(id)}
                  />
                  <DebtListMobileCards
                    results={results}
                    lastFourMonthLabels={lastFourMonthLabels}
                    isAdmin={isAdmin}
                    onDeleteDebt={(id) => deleteMutation.mutate(id)}
                  />
                </>
              )}

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
            </section>
          ) : null}
        </div>
      )}

      {isAdmin ? (
        <ImportModal
          open={importOpen}
          title="Импорт долгов"
          description={
            <p>
              CSV или XLSX. Обязательная колонка с ФИО (как в шаблоне: «ФИО»). Также поддерживаются
              колонки: БОТ, Направление, тг, @, Общая сумма, Сколько уже заплатил, Сколько еще осталось,
              Дата акта, НДС 5%.
            </p>
          }
          file={importFile}
          onFileChange={setImportFile}
          onExitComplete={() => {
            setImportOpen(false)
            setImportFile(null)
            debtImport.setImportTaskId(null)
          }}
          onSubmit={() => {
            if (importFile) {
              debtImport.importMutation.mutate(importFile)
            }
          }}
          pending={debtImport.importMutation.isPending}
          taskId={debtImport.importTaskId}
          titleId={importModalTitleId}
        />
      ) : null}
    </div>
  )
}

export default DebtsListPage
