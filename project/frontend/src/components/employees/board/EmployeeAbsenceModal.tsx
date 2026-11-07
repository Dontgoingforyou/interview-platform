import { useEffect, useState } from 'react'

import { ABSENCE_STATUS_OPTIONS } from '../../../constants/absenceStatuses'
import { useBodyScrollLock } from '../../../hooks/useBodyScrollLock'
import { useModalEnterExit } from '../../../hooks/useModalEnterExit'

interface EmployeeAbsenceModalProps {
  open: boolean
  initialStatus: string
  initialNotes: string
  onExitComplete: () => void
  onSave: (status: string, notes: string) => Promise<void>
  onRemove: () => Promise<void>
}

export default function EmployeeAbsenceModal({
  open,
  initialStatus,
  initialNotes,
  onExitComplete,
  onSave,
  onRemove,
}: EmployeeAbsenceModalProps) {
  const modal = useModalEnterExit(open, { onExitComplete })
  useBodyScrollLock(modal.shouldMount)

  const [status, setStatus] = useState(initialStatus)
  const [notes, setNotes] = useState(initialNotes)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) {
      setStatus(initialStatus || ABSENCE_STATUS_OPTIONS[0].value)
      setNotes(initialNotes)
    }
  }, [open, initialStatus, initialNotes])

  useEffect(() => {
    if (!modal.shouldMount) {
      return
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        modal.requestClose()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [modal, modal.shouldMount])

  if (!modal.shouldMount) {
    return null
  }

  async function handleSave() {
    setBusy(true)
    try {
      await onSave(status, notes)
      modal.requestClose()
    } finally {
      setBusy(false)
    }
  }

  async function handleRemove() {
    setBusy(true)
    try {
      await onRemove()
      modal.requestClose()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className={`absence-modal-overlay ${modal.overlayOpenClass}`}
      role="presentation"
      onClick={() => modal.requestClose()}
    >
      <div
        className="absence-modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="absence-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absence-modal-header">
          <h3 id="absence-modal-title">Статус отсутствия</h3>
          <button
            type="button"
            className="absence-modal-close"
            onClick={() => modal.requestClose()}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>
        <div className="absence-modal-body">
          <label htmlFor="absence-status-select">Тип отсутствия</label>
          <select
            id="absence-status-select"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            disabled={busy}
          >
            {ABSENCE_STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <label htmlFor="absence-notes">Комментарий</label>
          <textarea
            id="absence-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            disabled={busy}
          />
        </div>
        <div className="absence-modal-footer">
          <button type="button" className="absence-modal-save" onClick={handleSave} disabled={busy}>
            Сохранить
          </button>
          <button
            type="button"
            className="absence-modal-cancel"
            onClick={() => modal.requestClose()}
            disabled={busy}
          >
            Отмена
          </button>
          <button type="button" className="absence-modal-remove" onClick={handleRemove} disabled={busy}>
            Снять статус
          </button>
        </div>
      </div>
    </div>
  )
}
