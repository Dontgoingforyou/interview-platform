import { Fragment } from 'react'

import { InlineError } from '../../ui'
import LoadingLine from '../../ui/LoadingLine'
import { TableScroll } from '../../ui'
import type { AdminKpiResponse } from '../../../types/employee'
import AdminKpiDetailsTable from './AdminKpiDetailsTable'
import AdminKpiMobileCards from './AdminKpiMobileCards'

interface AdminKpiResultsSectionProps {
  applied: boolean
  isLoading: boolean
  isSuccess: boolean
  data: AdminKpiResponse | undefined
  openRows: Set<number>
  onToggleRow: (index: number) => void
  showGenericFetchError: boolean
}

export default function AdminKpiResultsSection({
  applied,
  isLoading,
  isSuccess,
  data,
  openRows,
  onToggleRow,
  showGenericFetchError,
}: AdminKpiResultsSectionProps) {
  if (!applied) {
    return null
  }

  if (isLoading) {
    return <LoadingLine message="Загрузка отчёта…" />
  }

  if (showGenericFetchError) {
    return <InlineError message="Не удалось загрузить отчёт." />
  }

  if (!isSuccess || !data) {
    return null
  }

  if (data.results.length === 0) {
    return (
      <div className="alert alert-info admin-report-alert">
        За выбранный период ни у одного менеджера KPI не достигало <strong>{data.min_kpi}</strong>.
        Попробуйте расширить диапазон дат или снизить порог KPI.
      </div>
    )
  }

  return (
    <>
      <div className="admin-report-header">
        <h2 className="admin-report-title">
          Найдено менеджеров:{' '}
          <strong className="text-accent-blue">{data.results.length}</strong>
          &nbsp;·&nbsp; КПИ ≥ <strong className="text-accent-green">{data.min_kpi}</strong>
          &nbsp;·&nbsp; Период:{' '}
          <strong>
            {data.date_from} — {data.date_to}
          </strong>
        </h2>
      </div>
      <div className="admin-kpi-table-wrap">
        <TableScroll className="table-scroll--plain">
          <table className="data-table interviews-data-table">
            <thead>
              <tr>
                <th className="col-num">#</th>
                <th>Менеджер</th>
                <th className="col-count-md td-center">Недель с KPI ≥ {data.min_kpi}</th>
                <th className="col-count-md td-center">Активных разработчиков</th>
                <th className="col-toggle td-center">Детали</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((item, idx) => (
                <Fragment key={item.manager.email}>
                  <tr
                    className="kpi-row"
                    onClick={() => onToggleRow(idx)}
                    onKeyDown={(e) => e.key === 'Enter' && onToggleRow(idx)}
                    role="button"
                    tabIndex={0}
                  >
                    <td className="td-muted">{idx + 1}</td>
                    <td>
                      <strong>{item.manager.full_name}</strong>
                    </td>
                    <td className="td-center">
                      <span className="kpi-badge">{item.qualifying_weeks_count}</span>
                    </td>
                    <td className="td-secondary-center">{item.total_active_devs}</td>
                    <td className="td-center">
                      <span className="toggle-icon-kpi">{openRows.has(idx) ? '▾' : '▸'}</span>
                    </td>
                  </tr>
                  {openRows.has(idx) ? (
                    <tr className="kpi-details-row">
                      <td colSpan={5}>
                        <AdminKpiDetailsTable row={item} />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </TableScroll>
      </div>
      <AdminKpiMobileCards data={data} openRows={openRows} onToggleRow={onToggleRow} />
    </>
  )
}
