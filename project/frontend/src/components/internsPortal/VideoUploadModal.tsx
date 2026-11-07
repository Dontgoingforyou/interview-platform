import { useEffect, useId } from 'react'

import { useBodyScrollLock } from '../../hooks/useBodyScrollLock'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'

export type VideoUploadModalPhase = 'pick' | 'uploading' | 'error'

interface VideoUploadModalProps {
  open: boolean
  interviewLabel: string
  interviewId: number | null
  file: File | null
  onFileChange: (f: File | null) => void
  onExitComplete: () => void
  onSubmit: () => void
  phase: VideoUploadModalPhase
  /** Прогресс отправки файла браузером на сервер (0–100). Отображается в фазе uploading. */
  uploadPercent: number
  errorMessage: string | null
}

/** Модалка загрузки видеозаписи собеседования (портал студента). */
function VideoUploadModal({
  open,
  interviewLabel,
  interviewId,
  file,
  onFileChange,
  onExitComplete,
  onSubmit,
  phase,
  uploadPercent,
  errorMessage,
}: VideoUploadModalProps) {
  const titleId = useId()
  const modal = useModalEnterExit(open, { onExitComplete })
  useBodyScrollLock(modal.shouldMount)

  const busy = phase === 'uploading'

  useEffect(() => {
    if (!modal.shouldMount) {
      return
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) {
        modal.requestClose()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [modal, modal.shouldMount, busy])

  if (!modal.shouldMount) {
    return null
  }

  const showFileInput = phase === 'pick' || phase === 'error'

  return (
    <div
      className={`import-modal-overlay ${modal.overlayOpenClass}`}
      role="presentation"
      onClick={() => {
        if (!busy) {
          modal.requestClose()
        }
      }}
    >
      <div
        className="import-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId}>Загрузить запись собеседования</h2>
        <p className="form-text">{interviewLabel}</p>

        {showFileInput ? (
          <>
            <label className="form-label" htmlFor="portal-video-file">
              Файл видео
            </label>
            <input
              id="portal-video-file"
              type="file"
              className="form-input"
              accept=".mp4,.mov,.avi,.mkv,.webm,.flv,.wmv"
              disabled={busy}
              onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
            />
            <p className="form-text">
              Допустимые форматы: mp4, mov, avi, mkv, webm, flv, wmv. Максимум 10 ГБ.
            </p>
          </>
        ) : null}

        {phase === 'uploading' ? (
          <div className="upload-progress-wrap import-modal__progress">
            <p className="form-text">Отправка файла на сервер…</p>
            {uploadPercent > 0 ? (
              <div className="import-progress-track">
                <div className="import-progress-bar" style={{ width: `${uploadPercent}%` }}>
                  {uploadPercent}%
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {phase === 'error' && errorMessage ? (
          <div className="upload-progress-wrap import-modal__progress">
            <p className="form-text text-danger">{errorMessage}</p>
          </div>
        ) : null}

        <div className="form-actions import-modal__actions">
          {phase === 'pick' || phase === 'error' ? (
            <>
              <button
                type="button"
                className="btn-primary"
                disabled={!file || !interviewId || busy}
                onClick={onSubmit}
              >
                Загрузить
              </button>
              <button type="button" className="btn-secondary" disabled={busy} onClick={() => modal.requestClose()}>
                Отмена
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn-secondary"
              disabled={busy}
              onClick={() => modal.requestClose()}
            >
              Закрыть
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default VideoUploadModal
