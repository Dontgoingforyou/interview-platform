import { useState } from 'react'

import { INTERN_STATUS_ACTIVE } from '../../../constants/internStatuses'
import { formatRuDate } from '../../../utils/dateFormat'
import { employeeBoardDirectionLabel } from '../../../utils/employees/employeeBoard'
import type { BoardAbsenceInfo, BoardInternRow } from '../../../types/employee'
import EmployeeStatusSelect from './EmployeeStatusSelect'
import EmployeeWeekCell from './EmployeeWeekCell'

interface EmployeeInternMobileCardsProps {
  rows: BoardInternRow[]
  recentWeeks: [string, string][]
  directionsDict: Record<string, string>
  coefficients: number[] | null
  isAdmin: boolean
  /** Разрешены ли изменения: false для HR/outstaff */
  canWrite: boolean
  statusPending?: boolean
  onStatusChange: (internId: number, value: string) => void
  onOpenAbsence: (payload: { internId: number; weekStart: string; info: BoardAbsenceInfo | null }) => void
  onSaveAdminCount: (internId: number, weekStart: string, value: number | null) => Promise<void>
  statusSavedFlashInternId?: number | null
}

function InternMobileCard({
  item,
  recentWeeks,
  directionsDict,
  coefficients,
  isAdmin,
  canWrite,
  statusPending,
  onStatusChange,
  onOpenAbsence,
  onSaveAdminCount,
  statusSavedFlash,
}: {
  item: BoardInternRow
  recentWeeks: [string, string][]
  directionsDict: Record<string, string>
  coefficients: number[] | null
  isAdmin: boolean
  canWrite: boolean
  statusPending: boolean
  onStatusChange: (v: string) => void
  onOpenAbsence: (payload: { internId: number; weekStart: string; info: BoardAbsenceInfo | null }) => void
  onSaveAdminCount: (weekStart: string, value: number | null) => Promise<void>
  statusSavedFlash: boolean
}) {
  const [weeksOpen, setWeeksOpen] = useState(false)
  const isActive = item.status === INTERN_STATUS_ACTIVE
  const hasCoefficients = coefficients && coefficients.length > 0

  return (
    <article className="intern-mobile-card" id={`intern-card-${item.intern.id}`}>
      <div className="intern-mobile-card__head">
        <strong className="intern-mobile-card__name">{item.intern.full_name}</strong>
        <EmployeeStatusSelect
          status={item.status}
          statusDisplay={item.status_display}
          onChange={onStatusChange}
          disabled={!canWrite || statusPending}
          saveFlash={statusSavedFlash}
        />
      </div>

      <dl className="intern-mobile-card__dl">
        <div>
          <dt>Дата выхода на собесы</dt>
          <dd>{formatRuDate(item.intern.real_interview_date) || '—'}</dd>
        </div>
        <div>
          <dt>Направление</dt>
          <dd>{employeeBoardDirectionLabel(directionsDict, item.intern.direction_id) || '—'}</dd>
        </div>
      </dl>

      {isActive ? (
        <>
          <button
            type="button"
            className="intern-mobile-card__weeks-toggle"
            onClick={() => setWeeksOpen((v) => !v)}
            aria-expanded={weeksOpen}
            aria-label={weeksOpen ? 'Скрыть недели' : 'Показать недели'}
          >
            Недели
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              aria-hidden
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          <div className={`intern-weeks-collapse${weeksOpen ? '' : ' is-collapsed'}`}>
            <div className="intern-weeks-collapse__inner">
              <div className="intern-mobile-card__weeks">
                <table className="intern-mobile-weeks-table">
                  <thead>
                    <tr>
                      <th>Период</th>
                      <th className="td-center">Собесы</th>
                      {hasCoefficients && <th className="td-center intern-mobile-coeff-th">Коэф.</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {item.recent_weeks_data.map((wd, i) => {
                      const [ws, we] = recentWeeks[i] ?? [wd.week_start, '']
                      return (
                        <tr key={wd.week_start}>
                          <td className="intern-week-period">
                            {ws}–{we}
                          </td>
                          <EmployeeWeekCell
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
                            onSaveAdminCount={(v) => onSaveAdminCount(wd.week_start, v)}
                          />
                          {hasCoefficients && (
                            <td className="intern-mobile-coeff-cell">
                              {coefficients[i] !== undefined ? coefficients[i].toFixed(2) : '—'}
                            </td>
                          )}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      ) : (
        <p className="intern-mobile-card__inactive-note">Не активен</p>
      )}
    </article>
  )
}

export default function EmployeeInternMobileCards({
  rows,
  recentWeeks,
  directionsDict,
  coefficients,
  isAdmin,
  canWrite,
  statusPending = false,
  onStatusChange,
  onOpenAbsence,
  onSaveAdminCount,
  statusSavedFlashInternId,
}: EmployeeInternMobileCardsProps) {
  if (rows.length === 0) {
    return <p className="td-empty-state">Нет сотрудников.</p>
  }

  return (
    <ul className="intern-mobile-cards-list">
      {rows.map((item) => (
        <li key={item.intern.id}>
          <InternMobileCard
            item={item}
            recentWeeks={recentWeeks}
            directionsDict={directionsDict}
            coefficients={coefficients}
            isAdmin={isAdmin}
            canWrite={canWrite}
            statusPending={statusPending}
            onStatusChange={(v) => onStatusChange(item.intern.id, v)}
            onOpenAbsence={onOpenAbsence}
            onSaveAdminCount={(ws, v) => onSaveAdminCount(item.intern.id, ws, v)}
            statusSavedFlash={statusSavedFlashInternId === item.intern.id}
          />
        </li>
      ))}
    </ul>
  )
}
