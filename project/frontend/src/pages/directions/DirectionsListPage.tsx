import { useQuery } from '@tanstack/react-query'
import { useCallback, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { getDirections } from '../../api/referenceApi'
import DirectionObservationsBlock from '../../components/directions/DirectionObservationsBlock'
import DirectionMetricsMainGrid from '../../components/directions/analytics/DirectionMetricsMainGrid'
import DirectionInterviewsByDirectionChart from '../../components/directions/charts/DirectionInterviewsByDirectionChart'
import DirectionInterviewsByMonthChart from '../../components/directions/charts/DirectionInterviewsByMonthChart'
import DirectionMetricsFilters from '../../components/directions/filters/DirectionMetricsFilters'
import DirectionMetricsMobileCards from '../../components/directions/list/DirectionMetricsMobileCards'
import DirectionMetricsTable from '../../components/directions/list/DirectionMetricsTable'
import { CollapsibleSection, InlineError, ListPageSkeleton, LoadingLine, PageIntroCard } from '../../components/ui'
import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { DIRECTION_METRICS_MAIN } from '../../constants/directionMetrics'
import { useDirectionsMetricsPage } from '../../hooks/directions/useDirectionsMetricsPage'
import { useAuthStore } from '../../store/authStore'
import type { SelectOption } from '../../types/common'
import { isAdminUser } from '../../utils/authRoles'
import { parseDirectionMetricsFromSearchParams } from '../../utils/directions/directionMetricsParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { computeManagersInterviewsChartPlotHeight } from '../../utils/managers/managersChartLayout'

/**
 * Метрики по направлениям: карточки, фильтры, таблица, графики, наблюдения.
 */
function DirectionsListPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseDirectionMetricsFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const filtersPanelId = useId()
  const observationsHeadingId = useId()

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const directionOptions: SelectOption<number>[] = useMemo(
    () => (directionsQuery.data ?? []).map((d) => ({ value: d.id, label: d.name })),
    [directionsQuery.data],
  )

  const { metricsQuery, observationsQuery } = useDirectionsMetricsPage(filters)

  const setSearchParamsNav = useCallback(
    (next: URLSearchParams, opts?: { replace?: boolean }) => {
      setSearchParams(next, {
        replace: opts?.replace ?? true,
        preventScrollReset: true,
      })
    },
    [setSearchParams],
  )

  const metricsRows = metricsQuery.data?.metrics_data ?? metricsQuery.data?.metrics ?? []
  const isInitialLoad = metricsQuery.isLoading && !metricsQuery.data

  /** Одна высота для пары графиков в ряду. */
  const directionsChartsPlotHeight = useMemo(() => {
    const d = metricsQuery.data
    if (!d) {
      return undefined
    }
    const n = d.chart_directions?.labels.length ?? 0
    const fromBar = computeManagersInterviewsChartPlotHeight(n)
    return Math.max(fromBar, 420)
  }, [metricsQuery.data])

  const directionsSkeletonHead = (
    <thead className="table-light">
      <tr>
        <th className="col-dir-name" scope="col">
          Направление
        </th>
        <th className="col-dir-num" scope="col">
          Интервью
        </th>
        <th className="col-dir-num" scope="col">
          Тех интервью
        </th>
        <th className="col-dir-num" scope="col">
          Кандидатов
        </th>
        <th className="col-dir-num" scope="col">
          Конверсия
        </th>
        <th className="col-dir-num" scope="col">
          Предстоящие
        </th>
        <th className="col-dir-date" scope="col">
          Последнее интервью
        </th>
      </tr>
    </thead>
  )

  return (
    <div className="page directions-list-page list-page">
      <PageIntroCard title="Метрики по направлениям">
        <p>
          Аналитика по собеседованиям, сгруппированным по направлениям: количество интервью, уникальных
          кандидатов, конверсия из скрининга в технические, предстоящие собеседования и дата последнего
          прошедшего интервью.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <>
          <ListPageSkeleton
            colCount={7}
            tableHead={directionsSkeletonHead}
            metricCardsCount={DIRECTION_METRICS_MAIN.length}
            showFiltersSkeleton
            showChartsRowSkeleton
            dataTableClassName={`data-table data-table--directions ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
            scrollClassName="table-scroll--plain"
          />
          <div className="interns-page-ready" aria-hidden="true">
            <div className="skeleton" style={{ height: '1.25rem', width: 'min(320px, 50%)', margin: '1rem 0 0.75rem' }} />
            <div className="skeleton" style={{ height: '4.5rem', width: '100%', borderRadius: 8 }} />
          </div>
        </>
      ) : null}

      {!isInitialLoad ? (
        <div className="interns-page-ready">
          {metricsQuery.isError ? (
            <InlineError message="Не удалось загрузить метрики. Попробуйте обновить страницу." />
          ) : null}
          {metricsQuery.data ? <DirectionMetricsMainGrid analytics={metricsQuery.data} /> : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="directions-filters-heading"
          >
            <DirectionMetricsFilters
              filters={filters}
              directionOptions={directionOptions}
              directionsLoading={directionsQuery.isLoading}
              searchParams={searchParams}
              setSearchParams={setSearchParamsNav}
            />
          </CollapsibleSection>

          {metricsQuery.data ? (
            <div className="managers-charts-row directions-charts-row">
              <DirectionInterviewsByDirectionChart
                analytics={metricsQuery.data}
                plotHeight={directionsChartsPlotHeight}
              />
              <DirectionInterviewsByMonthChart
                analytics={metricsQuery.data}
                plotHeight={directionsChartsPlotHeight}
              />
            </div>
          ) : null}

          {isAdmin && metricsQuery.data ? (
            <div className="directions-new-direction-row">
              <Link to="/directions/new" className="btn-primary">
                + Новое направление
              </Link>
            </div>
          ) : null}

          {metricsQuery.isFetching && metricsQuery.data ? (
            <LoadingLine message="Обновление метрик…" />
          ) : null}

          {metricsQuery.data ? (
            <section
              className={withListDataRefreshingClass(
                'directions-table-section interns-list-section',
                isListBackgroundRefetch(metricsQuery.isFetching, Boolean(metricsQuery.data)),
              )}
              aria-label="Таблица метрик по направлениям"
            >
              {metricsRows.length === 0 ? (
                <p className="alert alert-info">Нет данных.</p>
              ) : (
                <>
                  <div className="directions-table-desktop">
                    <DirectionMetricsTable
                      rows={metricsRows}
                      totalInterviews={metricsQuery.data.total_interviews}
                      totalTechInterviews={metricsQuery.data.total_tech_interviews_count}
                      totalCandidates={metricsQuery.data.total_candidates}
                      totalUpcoming={metricsQuery.data.total_upcoming}
                    />
                  </div>
                  <DirectionMetricsMobileCards rows={metricsRows} />
                </>
              )}
            </section>
          ) : null}

          <section
            className="managers-observations-section"
            aria-labelledby={observationsHeadingId}
          >
            <h2 id={observationsHeadingId}>Наблюдения по направлениям</h2>
            <DirectionObservationsBlock
              data={observationsQuery.data}
              isError={observationsQuery.isError}
            />
          </section>
        </div>
      ) : null}
    </div>
  )
}

export default DirectionsListPage
