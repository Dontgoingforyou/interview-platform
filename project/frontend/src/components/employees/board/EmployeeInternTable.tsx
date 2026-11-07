import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { INTERN_STATUS_ACTIVE } from '../../../constants/internStatuses'
import { TableScroll } from '../../ui'
import { employeeBoardDirectionLabel } from '../../../utils/employees/employeeBoard'
import { formatRuDate } from '../../../utils/dateFormat'
import type { BoardAbsenceInfo, BoardInternRow } from '../../../types/employee'
import EmployeeStatusSelect from './EmployeeStatusSelect'
import EmployeeWeekCell from './EmployeeWeekCell'
import EmployeeInternMobileCards from './EmployeeInternMobileCards'

export interface EmployeeInternTableProps {
  title: string
  recentWeeks: [string, string][]
  rows: BoardInternRow[]
  directionsDict: Record<string, string>
  coefficients: number[] | null
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
  /** Подсветить строку статуса после успешного PATCH */
  statusSavedFlashInternId?: number | null
}

export default function EmployeeInternTable({
  title,
  recentWeeks,
  rows,
  directionsDict,
  coefficients,
  isAdmin,
  canWrite,
  statusPending = false,
  onStatusChange,
  onOpenAbsence,
  onSaveAdminCount,
  statusSavedFlashInternId,
}: EmployeeInternTableProps) {
  const weekCount = recentWeeks.length
  const colSpanInactive = 4 + weekCount

  return (
    <section className="employee-table-section" aria-label={title}>
      <h2 className="employee-table-section-title">{title}</h2>
      <div className="employee-board-table-wrap">
        <TableScroll className="table-scroll--plain">
          <table className={`data-table data-table--employees employee-board-table ${DATA_TABLE_STICKY_LEADING}`}>
            <thead>
              <tr>
                <th className="emp-col-status">Статус</th>
                <th className="emp-col-name">ФИО</th>
                <th className="emp-col-date">Дата выхода на собесы</th>
                <th className="emp-col-direction">Направление</th>
                {recentWeeks.map((w, i) => (
                  <th key={`${w[0]}-${w[1]}-${i}`} className="emp-col-week">
                    {w[0]}–{w[1]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={colSpanInactive} className="text-center">
                    Нет сотрудников.
                  </td>
                </tr>
              ) : (
                rows.map((item) => (
                  <tr key={item.intern.id} id={`intern-${item.intern.id}`}>
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
                    <td>{employeeBoardDirectionLabel(directionsDict, item.intern.direction_id)}</td>
                    {item.status === INTERN_STATUS_ACTIVE ? (
                      item.recent_weeks_data.map((wd) => (
                        <EmployeeWeekCell
                          key={wd.week_start}
                          internId={item.intern.id}
                          weekStart={wd.week_start}
                          count={wd.count}
                          absenceInfo={wd.absence_info}
                          isAdmin={isAdmin}
                          canWrite={canWrite}
                          onOpenAbsence={() =>
                            onOpenAbsence({
                              internId: item.intern.id,
                              weekStart: wd.week_start,
                              info: wd.absence_info,
                            })
                          }
                          onSaveAdminCount={(v) => onSaveAdminCount(item.intern.id, wd.week_start, v)}
                        />
                      ))
                    ) : (
                      <td colSpan={weekCount} className="td-inactive-intern">
                        —
                      </td>
                    )}
                  </tr>
                ))
              )}
              {coefficients && coefficients.length > 0 ? (
                <tr className="kpi-coeff-row">
                  <td colSpan={4} className="kpi-coeff-label">
                    КОЭФФИЦИЕНТ:
                  </td>
                  {coefficients.map((c, i) => (
                    <td key={i} className="kpi-coeff-value">
                      <div className="interview-count-wrapper">
                        <span>{c.toFixed(2)}</span>
                        <span className="kpi-coeff-spacer" aria-hidden />
                      </div>
                    </td>
                  ))}
                </tr>
              ) : null}
            </tbody>
          </table>
        </TableScroll>
      </div>
      <EmployeeInternMobileCards
        rows={rows}
        recentWeeks={recentWeeks}
        directionsDict={directionsDict}
        coefficients={coefficients}
        isAdmin={isAdmin}
        canWrite={canWrite}
        statusPending={statusPending}
        onStatusChange={onStatusChange}
        onOpenAbsence={onOpenAbsence}
        onSaveAdminCount={onSaveAdminCount}
        statusSavedFlashInternId={statusSavedFlashInternId}
      />
    </section>
  )
}
