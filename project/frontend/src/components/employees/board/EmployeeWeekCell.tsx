import { useState } from 'react'

import type { BoardAbsenceInfo } from '../../../types/employee'

interface EmployeeWeekCellProps {
  internId: number
  weekStart: string
  count: number | string
  absenceInfo: BoardAbsenceInfo | null
  isAdmin: boolean
  /** Разрешены ли изменения: false для HR/outstaff — скрывает кнопку паузы */
  canWrite: boolean
  onOpenAbsence: () => void
  onSaveAdminCount: (value: number | null) => Promise<void>
}

/** Ячейка «число собесов за неделю» + кнопка отсутствия. */
export default function EmployeeWeekCell({
  internId,
  weekStart,
  count,
  absenceInfo,
  isAdmin,
  canWrite,
  onOpenAbsence,
  onSaveAdminCount,
}: EmployeeWeekCellProps) {
  const [editing, setEditing] = useState(false)
  const [input, setInput] = useState(String(count))
  const [saving, setSaving] = useState(false)

  const display = typeof count === 'number' ? String(count) : String(count)
  const title =
    absenceInfo?.notes?.trim() ? absenceInfo.notes : (absenceInfo?.status_display ?? undefined)

  async function commit() {
    if (!isAdmin) {
      return
    }
    const trimmed = input.trim()
    if (trimmed === display) {
      setEditing(false)
      return
    }
    const n = trimmed === '' ? null : parseInt(trimmed, 10)
    if (trimmed !== '' && Number.isNaN(n)) {
      setInput(display)
      setEditing(false)
      return
    }
    setSaving(true)
    try {
      await onSaveAdminCount(n)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <td
      className={`interview-count-cell${isAdmin ? ' editable-cell' : ''}`}
      title={title}
      data-intern-id={internId}
      data-week-start={weekStart}
      {...(absenceInfo
        ? {
            'data-absence-status': absenceInfo.status,
            'data-absence-status-display': absenceInfo.status_display,
          }
        : {})}
    >
      <div className="interview-count-wrapper">
        {!editing ? (
          <span
            className="interview-count-display"
            onClick={() => isAdmin && setEditing(true)}
            onKeyDown={(e) => e.key === 'Enter' && isAdmin && setEditing(true)}
            role={isAdmin ? 'button' : undefined}
            tabIndex={isAdmin ? 0 : undefined}
          >
            {display}
          </span>
        ) : (
          <span className="interview-count-edit">
            <input
              type="text"
              inputMode="numeric"
              className="interview-count-input"
              value={input}
              disabled={saving}
              onChange={(e) => setInput(e.target.value.replace(/\D/g, ''))}
              onBlur={() => commit()}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  void commit()
                }
                if (e.key === 'Escape') {
                  setInput(display)
                  setEditing(false)
                }
              }}
              autoFocus
            />
          </span>
        )}
        {canWrite && (
          <button
            type="button"
            className="absence-btn"
            title="Установить статус отсутствия"
            onClick={(e) => {
              e.stopPropagation()
              onOpenAbsence()
            }}
          >
            ⏸️
          </button>
        )}
      </div>
    </td>
  )
}
