import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'

interface ImportModalProps {
  open: boolean
  title: string
  description: ReactNode
  file: File | null
  onFileChange: (f: File | null) => void
  onExitComplete: () => void
  onSubmit: () => void
  pending: boolean
  taskId: string | null
  titleId: string
}

/** Модальное окно импорта CSV/XLSX с анимацией открытия/закрытия. */
function ImportModal({
  open,
  title,
  description,
  file,
  onFileChange,
  onExitComplete,
  onSubmit,
  pending,
  taskId,
  titleId,
}: ImportModalProps) {
  const modal = useModalEnterExit(open, { onExitComplete })
  useBodyScrollLock(modal.shouldMount)

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

  return (
    <div
      className={`import-modal-overlay ${modal.overlayOpenClass}`}
      role="presentation"
      onClick={() => modal.requestClose()}
    >
      <div
        className="import-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId}>{title}</h2>
        <div className="import-modal__desc">{description}</div>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
        />
        <div className="form-actions import-modal__actions">
          <button type="button" className="btn-primary" disabled={!file || pending} onClick={onSubmit}>
            Загрузить
          </button>
          <button type="button" className="btn-secondary" onClick={() => modal.requestClose()}>
            Закрыть
          </button>
        </div>
        {taskId ? (
          <p className="import-modal__task">Задача: {taskId}. Статус обновляется автоматически.</p>
        ) : null}
      </div>
    </div>
  )
}

export default ImportModal
