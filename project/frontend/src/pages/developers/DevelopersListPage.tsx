import { useCallback, useId, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import {
  downloadDevelopersChartExport,
  downloadDevelopersMetricsExport,
  downloadDevelopersTableExport,
} from '../../api/developersApi'
import { getDirections } from '../../api/referenceApi'
import DeveloperMetricsMainGrid from '../../components/developers/analytics/DeveloperMetricsMainGrid'
import DeveloperOffersByMonthChart from '../../components/developers/charts/DeveloperOffersByMonthChart'
import DeveloperFilters from '../../components/developers/filters/DeveloperFilters'
import DeveloperListDesktopTable from '../../components/developers/list/DeveloperListDesktopTable'
import DeveloperListMobileCards from '../../components/developers/list/DeveloperListMobileCards'
import DeveloperListTableHead from '../../components/developers/list/DeveloperListTableHead'
import Pagination from '../../components/Pagination'
import { CollapsibleSection, InlineError, ListPageSkeleton, PageIntroCard } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { DEVELOPER_METRICS_MAIN } from '../../constants/developerMetrics'
import { useDevelopersListPage } from '../../hooks/developers/useDevelopersListPage'
import { useMeaningfulListFilters } from '../../hooks/useMeaningfulListFilters'
import { parseDeveloperListFromSearchParams } from '../../utils/developers/developerListParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { applyTableSortToSearchParams, withClonedSearchParams } from '../../utils/listPageSearchParams'

/**
 * Разработчики за период: метрики, график, фильтры, таблица, экспорт в Excel.
 */
function DevelopersListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseDeveloperListFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [exportBusy, setExportBusy] = useState<string | null>(null)
  const filtersPanelId = useId()

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const hasActiveSemanticFilters = useMeaningfulListFilters(searchParams)

  const { analyticsQuery, listQuery, count, totalPages, currentPage, results } =
    useDevelopersListPage(filters)

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
      setSearchParams(withClonedSearchParams(searchParams, mut), {
        replace: true,
        preventScrollReset: true,
      })
    },
    [searchParams, setSearchParams],
  )

  const setSearchParamsNav = useCallback(
    (next: URLSearchParams, opts?: { replace?: boolean }) => {
      setSearchParams(next, {
        replace: opts?.replace ?? true,
        preventScrollReset: true,
      })
    },
    [setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      updateParams((next) => {
        applyTableSortToSearchParams(next, field, 'asc')
      })
    },
    [updateParams],
  )

  const runExport = useCallback(
    async (kind: 'table' | 'metrics' | 'chart', fn: () => Promise<void>) => {
      try {
        setExportBusy(kind)
        await fn()
      } catch {
        toast.error('Не удалось скачать файл')
      } finally {
        setExportBusy(null)
      }
    },
    [],
  )

  const isInitialLoad =
    (analyticsQuery.isLoading && !analyticsQuery.data) || (listQuery.isLoading && !listQuery.data)

  return (
    <div className="page developers-list-page">
      <PageIntroCard title="Разработчики за выбранный период">
        <p>
          Объединяем данные по собеседованиям и офферам: сколько интервью проходит каждый специалист,
          есть ли будущие встречи и кому предложили работу.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <ListPageSkeleton
          colCount={4}
          tableHead={<DeveloperListTableHead filters={filters} onToggleSort={toggleSort} />}
          metricCardsCount={DEVELOPER_METRICS_MAIN.length}
          showFiltersSkeleton
          dataTableClassName={`data-table data-table--developers ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
          scrollClassName="table-scroll--plain developers-table-desktop developers-table-scroll"
        />
      ) : null}

      {!isInitialLoad ? (
        <div className="interns-page-ready">
          {analyticsQuery.isError ? (
            <InlineError message="Не удалось загрузить метрики." />
          ) : null}
          {analyticsQuery.data ? (
            <DeveloperMetricsMainGrid
              analytics={analyticsQuery.data}
              titleEnd={
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={exportBusy !== null}
                  onClick={() => runExport('metrics', downloadDevelopersMetricsExport)}
                >
                  {exportBusy === 'metrics' ? '…' : null} Скачать метрики (Excel)
                </button>
              }
            />
          ) : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="developers-filters-heading"
          >
            <DeveloperFilters
              filters={filters}
              directionOptions={directionOptions}
              directionsLoading={directionsQuery.isLoading}
              searchParams={searchParams}
              setSearchParams={setSearchParamsNav}
            />
          </CollapsibleSection>

          {listQuery.isFetching && listQuery.data ? (
            <LoadingLine message="Обновление списка…" />
          ) : null}
          {listQuery.isError ? (
            <InlineError message="Не удалось загрузить список. Попробуйте обновить страницу." />
          ) : null}

          {hasActiveSemanticFilters && listQuery.data ? (
            <p className="filter-results-summary interns-filter-summary">
              Найдено записей: <strong>{count}</strong>
            </p>
          ) : null}

          {!listQuery.isLoading && !listQuery.isError ? (
            <section
              className={withListDataRefreshingClass(
                'developers-list-section interns-list-section',
                isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
              )}
            >
              <div className="developers-table-export-row">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={exportBusy !== null}
                  onClick={() => runExport('table', () => downloadDevelopersTableExport(filters))}
                >
                  {exportBusy === 'table' ? '…' : null} Скачать таблицу (Excel)
                </button>
              </div>

              {results.length === 0 ? (
                <p className="alert alert-info">Нет данных о разработчиках с офферами.</p>
              ) : (
                <>
                  <DeveloperListDesktopTable
                    filters={filters}
                    onToggleSort={toggleSort}
                    results={results}
                  />
                  <DeveloperListMobileCards results={results} />
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

          <section className="developers-charts-section" aria-labelledby="developers-charts-heading">
            <div className="developers-section-header">
              <h2 id="developers-charts-heading">Графики</h2>
              <button
                type="button"
                className="btn-secondary"
                disabled={exportBusy !== null}
                onClick={() => runExport('chart', downloadDevelopersChartExport)}
              >
                {exportBusy === 'chart' ? '…' : null} Скачать график (Excel)
              </button>
            </div>
            {analyticsQuery.data ? (
              <div className="chart-card developers-chart-card">
                <h3 className="developers-chart-title">Активность по месяцам (количество офферов)</h3>
                <DeveloperOffersByMonthChart analytics={analyticsQuery.data} />
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </div>
  )
}

export default DevelopersListPage
