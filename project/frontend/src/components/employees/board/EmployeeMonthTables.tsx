import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { INTERN_STATUS_ACTIVE } from '../../../constants/internStatuses'
import { TableScroll } from '../../ui'
import { employeeBoardDirectionLabel } from '../../../utils/employees/employeeBoard'
import { formatRuDate } from '../../../utils/dateFormat'
import type { BoardAbsenceInfo, ManagerBoardResponse } from '../../../types/employee'
import EmployeeStatusSelect from './EmployeeStatusSelect'
import EmployeeWeekCell from './EmployeeWeekCell'

interface EmployeeMonthTablesProps {
  board: ManagerBoardResponse
  isAdmin: boolean
  /** Разрешены ли изменения: false для HR/outstaff */
  canWrite: boolean
  statusPending?: boolean
  onStatusChange: (internId: number, value: string) => void
  onOpenAbsence: (payload: {
    internId: number
    weekStart: string
    info: BoardAbsenceInfo | null
  }) => void
  onSaveAdminCount: (internId: number, weekStart: string, value: number | null) => Promise<void>
  statusSavedFlashInternId?: number | null
}

/** Таблицы по месяцам («все недели»). */
export default function EmployeeMonthTables({
  board,
  isAdmin,
  canWrite,
  statusPending = false,
  onStatusChange,
  onOpenAbsence,
  onSaveAdminCount,
  statusSavedFlashInternId,
}: EmployeeMonthTablesProps) {
  const months = Object.keys(board.all_months_formatted)

  return (
    <div className="employee-month-tables">
      {months.map((month) => {
        const weeks = board.all_months_formatted[month] ?? []
        const rows = board.all_interns.filter((r) => r.month === month)
        const weekCount = weeks.length

        return (
          <div key={month} className="month-section">
            <div className="month-header">{month}</div>
            {rows.length === 0 ? (
              <p className="employee-month-empty" role="status">
                Нет данных
              </p>
            ) : (
              <TableScroll className="table-scroll--plain">
                <table className={`data-table data-table--employees employee-board-table ${DATA_TABLE_STICKY_LEADING}`}>
                  <thead>
                    <tr>
                      <th className="emp-col-status">Статус</th>
                      <th className="emp-col-name">ФИО</th>
                      <th className="emp-col-date">Дата выхода на собесы</th>
                      <th className="emp-col-direction">Направление</th>
                      {weeks.map((w, i) => (
                        <th key={`${month}-w-${i}`} className="emp-col-week">
                          {w[0] === '—' && w[1] === '—' ? '—' : `${w[0]}–${w[1]}`}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((item) => (
                      <tr key={`${month}-${item.intern.id}`}>
                        <td>
                          <EmployeeStatusSelect
                            status={item.status}
                            statusDisplay={item.status_display}
                            onChange={(v) => onStatusChange(item.intern.id, v)}
                            disabled={!canWrite || statusPending}
                            saveFlash={statusSavedFlashInternId === item.intern.id}
                          />
                        </td>
                        <td>{item.intern.full_name}</td>
                        <td>{formatRuDate(item.intern.real_interview_date)}</td>
                        <td>{employeeBoardDirectionLabel(board.directions_dict, item.intern.direction_id)}</td>
                        {item.status === INTERN_STATUS_ACTIVE ? (
                          item.month_weeks_data.map((wd, idx) =>
                            wd.week_start ? (
                              <EmployeeWeekCell
                                key={`${wd.week_start}-${idx}`}
                                internId={item.intern.id}
                                weekStart={wd.week_start}
                                count={wd.count}
                                absenceInfo={wd.absence_info}
                                isAdmin={isAdmin}
                                canWrite={canWrite}
                                onOpenAbsence={() =>
                                  onOpenAbsence({
                                    internId: item.intern.id,
                                    weekStart: wd.week_start!,
                                    info: wd.absence_info,
                                  })
                                }
                                onSaveAdminCount={(v) =>
                                  onSaveAdminCount(item.intern.id, wd.week_start!, v)
                                }
                              />
                            ) : (
                              <td key={`pad-${idx}`}>{wd.count}</td>
                            ),
                          )
                        ) : (
                          <td colSpan={weekCount || 5} className="td-inactive-intern">
                            —
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableScroll>
            )}
          </div>
        )
      })}
    </div>
  )
}
