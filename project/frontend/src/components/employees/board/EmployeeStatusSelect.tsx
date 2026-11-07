import { useEffect, useRef, useState } from 'react'

import {
  INTERN_STATUS_ACTIVE,
  INTERN_STATUS_LEFT,
  INTERN_STATUS_OFFER,
} from '../../../constants/internStatuses'

interface EmployeeStatusSelectProps {
  status: string
  statusDisplay: string
  onChange: (newStatus: string) => void
  disabled?: boolean
  /** Краткая подсветка после успешного сохранения на сервере */
  saveFlash?: boolean
}

const OPTIONS = [
  { value: INTERN_STATUS_ACTIVE, label: 'Активный' },
  { value: INTERN_STATUS_LEFT, label: 'Ушёл' },
  { value: INTERN_STATUS_OFFER, label: 'Оффер' },
]

const STATUS_CLASS: Record<string, string> = {
  [INTERN_STATUS_ACTIVE]: 'status-active',
  [INTERN_STATUS_OFFER]: 'status-offer',
  [INTERN_STATUS_LEFT]: 'status-left',
}

export default function EmployeeStatusSelect({
  status,
  statusDisplay,
  onChange,
  disabled,
  saveFlash,
}: EmployeeStatusSelectProps) {
  const [editing, setEditing] = useState(false)
  const selectRef = useRef<HTMLSelectElement>(null)

  useEffect(() => {
    if (editing) {
      selectRef.current?.focus()
    }
  }, [editing])

  const badgeClass = STATUS_CLASS[status] ?? 'status-left'

  function handleBadgeClick() {
    if (!disabled) {
      setEditing(true)
    }
  }

  function handleBadgePointerDown(e: React.PointerEvent<HTMLSpanElement>) {
    if (disabled) {
      return
    }
    e.preventDefault()
    setEditing(true)
  }

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    onChange(e.target.value)
    setEditing(false)
  }

  function handleBlur() {
    setTimeout(() => setEditing(false), 0)
  }

  return (
    <div className="status-editable">
      {editing ? (
        <select
          ref={selectRef}
          className="status-select"
          value={status}
          disabled={disabled}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-label={`Статус: ${statusDisplay}`}
        >
          {OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      ) : (
        <span
          className={`status-label ${badgeClass}${saveFlash ? ' status-label--save-flash' : ''}`}
          role="button"
          tabIndex={disabled ? undefined : 0}
          onPointerDown={handleBadgePointerDown}
          onKeyDown={(e) => e.key === 'Enter' && handleBadgeClick()}
          aria-label={`Статус: ${statusDisplay}. Нажмите для изменения`}
        >
          {statusDisplay}
        </span>
      )}
    </div>
  )
}
