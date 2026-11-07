import { Fragment } from 'react'

import { TableScroll } from '../../ui'
import type { AdminDevelopersResponse } from '../../../types/employee'
import AdminDevelopersInternList from './AdminDevelopersInternList'
import AdminDevelopersMobileCards from './AdminDevelopersMobileCards'

interface AdminDevelopersReportProps {
  data: AdminDevelopersResponse
  showHidden: boolean
  onShowHiddenChange: (show: boolean) => void
  openRows: Set<number>
  onToggleListRow: (index: number) => void
  isTogglePending: boolean
  onSetManagerActive: (email: string, isActive: boolean) => void
}

export default function AdminDevelopersReport({
  data,
  showHidden,
  onShowHiddenChange,
  openRows,
  onToggleListRow,
  isTogglePending,
  onSetManagerActive,
}: AdminDevelopersReportProps) {
  return (
    <>
      <div className="admin-report-header">
        <h2 className="admin-report-title">
          Всего менеджеров: <strong className="text-accent-blue">{data.results.length}</strong>
          &nbsp;·&nbsp; Всего активных разработчиков:{' '}
          <strong className="text-accent-green">{data.total_active}</strong>
        </h2>
        {data.hidden_count > 0 || showHidden ? (
          <div className="dev-header-actions">
            {showHidden ? (
              <button type="button" className="btn-muted-sm" onClick={() => onShowHiddenChange(false)}>
                Скрыть скрытых ({data.hidden_count})
              </button>
            ) : (
              <button type="button" className="btn-muted-sm" onClick={() => onShowHiddenChange(true)}>
                Показать скрытых ({data.hidden_count})
              </button>
            )}
          </div>
        ) : null}
      </div>
      <div className="admin-developers-table-wrap">
        <TableScroll className="table-scroll--plain">
          <table className="data-table interviews-data-table">
            <thead>
              <tr>
                <th className="col-num">#</th>
                <th>Менеджер</th>
                <th className="col-count-lg td-center">Активных разработчиков</th>
                <th className="col-toggle td-center">Список</th>
                <th className="col-toggle td-center">Скрыть</th>
              </tr>
            </thead>
            <tbody>
              {data.results.length === 0 ? (
                <tr>
                  <td colSpan={5} className="td-empty-state">
                    Нет активных менеджеров
                  </td>
                </tr>
              ) : (
                data.results.map((item, idx) => (
                  <Fragment key={item.manager.email}>
                    <tr
                      className={`dev-row${item.active_count === 0 ? ' dev-row-empty' : ''}`}
                      onClick={() => item.active_count > 0 && onToggleListRow(idx)}
                      onKeyDown={(e) => e.key === 'Enter' && item.active_count > 0 && onToggleListRow(idx)}
                      role={item.active_count > 0 ? 'button' : undefined}
                      tabIndex={item.active_count > 0 ? 0 : undefined}
                    >
                      <td className="td-muted">{idx + 1}</td>
                      <td>
                        <strong className={item.active_count === 0 ? 'text-muted-inline' : undefined}>
                          {item.manager.full_name}
                        </strong>
                      </td>
                      <td className="td-center">
                        {item.active_count > 0 ? (
                          <span className="dev-count-badge">{item.active_count}</span>
                        ) : (
                          <span className="text-muted-inline">—</span>
                        )}
                      </td>
                      <td className="td-center">
                        {item.active_count > 0 ? (
                          <span className="toggle-icon-dev">{openRows.has(idx) ? '▾' : '▸'}</span>
                        ) : null}
                      </td>
                      <td className="td-center">
                        <button
                          type="button"
                          className="btn-hide-manager"
                          title="Скрыть менеджера из списков"
                          disabled={isTogglePending}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (
                              window.confirm(
                                `Скрыть менеджера «${item.manager.full_name}» из списков?`,
                              )
                            ) {
                              onSetManagerActive(item.manager.email, false)
                            }
                          }}
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                    {item.active_count > 0 && openRows.has(idx) ? (
                      <tr className="dev-list-row">
                        <td colSpan={5}>
                          <AdminDevelopersInternList interns={item.interns} />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))
              )}
            </tbody>
          </table>
        </TableScroll>
      </div>
      <AdminDevelopersMobileCards
        data={data}
        openRows={openRows}
        onToggleListRow={onToggleListRow}
        isTogglePending={isTogglePending}
        onSetManagerActive={onSetManagerActive}
      />

      {showHidden && data.hidden_results.length > 0 ? (
        <>
          <div className="admin-report-header admin-report-header--after-table">
            <h2 className="admin-report-title admin-title-muted">
              Скрытые менеджеры: <strong>{data.hidden_results.length}</strong>
            </h2>
          </div>
          <div className="admin-developers-table-wrap">
            <TableScroll className="table-scroll--plain">
              <table className="data-table interviews-data-table">
                <thead>
                  <tr>
                    <th className="col-num">#</th>
                    <th>Менеджер</th>
                    <th className="col-count-lg td-center">Активных разработчиков</th>
                    <th className="col-toggle td-center">Восстановить</th>
                  </tr>
                </thead>
                <tbody>
                  {data.hidden_results.map((item, idx) => (
                    <tr key={item.manager.email} className="dev-row dev-row-hidden">
                      <td className="td-muted">{idx + 1}</td>
                      <td>
                        <strong className="text-muted-inline">{item.manager.full_name}</strong>
                        <span className="dev-hidden-email">{item.manager.email}</span>
                      </td>
                      <td className="td-center">
                        {item.active_count > 0 ? (
                          <span className="dev-count-badge">{item.active_count}</span>
                        ) : (
                          <span className="text-muted-inline">—</span>
                        )}
                      </td>
                      <td className="td-center">
                        <button
                          type="button"
                          className="btn-restore-manager"
                          title="Восстановить менеджера"
                          disabled={isTogglePending}
                          onClick={() => onSetManagerActive(item.manager.email, true)}
                        >
                          ↩ Восстановить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
          </div>
          <AdminDevelopersMobileCards
            data={data}
            openRows={new Set()}
            onToggleListRow={() => {}}
            isTogglePending={isTogglePending}
            onSetManagerActive={onSetManagerActive}
            isHiddenSection
          />
        </>
      ) : null}
    </>
  )
}
