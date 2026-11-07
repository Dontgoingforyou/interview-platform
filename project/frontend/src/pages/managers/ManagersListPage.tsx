import { useMemo } from 'react'

import { InlineError, ListPageSkeleton, PageIntroCard } from '../../components/ui'
import ManagersInterviewsBarChart from '../../components/managers/charts/ManagersInterviewsBarChart'
import ManagersTeamActivityBarChart from '../../components/managers/charts/ManagersTeamActivityBarChart'
import ManagersMetricsMainGrid from '../../components/managers/analytics/ManagersMetricsMainGrid'
import ManagerListDesktopTable from '../../components/managers/list/ManagerListDesktopTable'
import ManagerListMobileCards from '../../components/managers/list/ManagerListMobileCards'
import ManagersObservationsSection from '../../components/managers/observations/ManagersObservationsSection'
import LoadingLine from '../../components/ui/LoadingLine'
import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { MANAGER_METRICS_MAIN } from '../../constants/managerMetrics'
import { useManagersDashboard } from '../../hooks/managers/useManagersDashboard'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { computeManagersInterviewsChartPlotHeight } from '../../utils/managers/managersChartLayout'

/**
 * Дашборд менеджеров: KPI, графики, таблица, наблюдения.
 */
function ManagersListPage() {
  const { analyticsQuery, observationsQuery, tableQuery } = useManagersDashboard()

  const isInitialLoad =
    (analyticsQuery.isLoading && !analyticsQuery.data) ||
    (tableQuery.isLoading && !tableQuery.data) ||
    (observationsQuery.isLoading && !observationsQuery.data)

  const managersChartsPlotHeight = useMemo(() => {
    if (!tableQuery.data?.length) {
      return undefined
    }
    return computeManagersInterviewsChartPlotHeight(tableQuery.data.length)
  }, [tableQuery.data])

  const managersSkeletonHead = (
    <thead className="table-light">
      <tr>
        <th className="col-manager-name">Менеджер</th>
        <th className="col-manager-total">Всего</th>
        <th className="col-manager-hot">Горячие</th>
        <th className="col-manager-active">В работе</th>
        <th className="col-manager-portfolio">В портфеле</th>
        <th className="col-manager-interviews">Интервью</th>
        <th className="col-manager-successful">Успешные</th>
        <th className="col-manager-directions">Направления</th>
        <th className="col-manager-last-date">Последнее интервью</th>
      </tr>
    </thead>
  )

  return (
    <div className="page managers-list-page">
      <PageIntroCard title="Команда менеджеров">
        <p>
          Сводный коэффициент работы команды: сколько кандидатов ведёт каждый менеджер, как часто проходят
          собеседования, какой процент доводится до результата и насколько быстро это происходит.
        </p>
        <p className="managers-metrics-hint">
          <strong>Метрики активности:</strong>{' '}
          <span className="text-hot">Горячие (7 дн.)</span> — активно проходят интервью сейчас |{' '}
          <span className="text-active">В работе (20 дн.)</span> — текущий активный пайплайн |{' '}
          <span className="text-portfolio">В портфеле (60 дн.)</span> — все кандидаты в работе
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <>
          <ListPageSkeleton
            colCount={9}
            tableHead={managersSkeletonHead}
            metricCardsCount={MANAGER_METRICS_MAIN.length}
            showChartsRowSkeleton
            dataTableClassName={`data-table data-table--managers ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
            scrollClassName="table-scroll--plain managers-table-desktop"
          />
          <section className="managers-observations-section" aria-hidden="true">
            <div className="skeleton" style={{ height: '1.25rem', width: 'min(280px, 55%)', marginBottom: '0.75rem' }} />
            <div className="skeleton" style={{ height: '5rem', width: '100%', borderRadius: 8 }} />
          </section>
        </>
      ) : null}

      {!isInitialLoad ? (
        <>
          {analyticsQuery.isError ? (
            <InlineError message="Не удалось загрузить метрики." />
          ) : analyticsQuery.data ? (
            <ManagersMetricsMainGrid analytics={analyticsQuery.data} />
          ) : null}

          {tableQuery.data && tableQuery.data.length > 0 && managersChartsPlotHeight != null ? (
            <div className="managers-charts-row">
              <ManagersInterviewsBarChart rows={tableQuery.data} plotHeight={managersChartsPlotHeight} />
              <ManagersTeamActivityBarChart rows={tableQuery.data} plotHeight={managersChartsPlotHeight} />
            </div>
          ) : null}

          {tableQuery.isFetching && tableQuery.data ? (
            <LoadingLine message="Обновление таблицы…" />
          ) : null}
          <section
            className={withListDataRefreshingClass(
              'managers-table-section',
              isListBackgroundRefetch(tableQuery.isFetching, Boolean(tableQuery.data)),
            )}
          >
            <h2>Менеджеры</h2>
            {tableQuery.isError ? <InlineError message="Не удалось загрузить таблицу менеджеров." /> : null}
            {tableQuery.data && tableQuery.data.length === 0 ? (
              <p className="alert alert-info">Нет данных о менеджерах.</p>
            ) : null}
            {tableQuery.data && tableQuery.data.length > 0 ? (
              <>
                <ManagerListDesktopTable rows={tableQuery.data} />
                <ManagerListMobileCards rows={tableQuery.data} />
              </>
            ) : null}
          </section>

          <section className="managers-observations-section" aria-labelledby="managers-observations-heading">
            <h2 id="managers-observations-heading">Наблюдения по менеджерам</h2>
            {observationsQuery.isError ? (
              <InlineError message="Не удалось загрузить наблюдения." />
            ) : (
              <ManagersObservationsSection data={observationsQuery.data} />
            )}
          </section>
        </>
      ) : null}
    </div>
  )
}

export default ManagersListPage
