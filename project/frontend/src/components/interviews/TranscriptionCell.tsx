import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import {
  getTranscriptionStatus,
  getTranscriptionText,
  postTranscribe,
} from '../../api/interviewsApi'
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'
import { toast } from '../../utils/toast'

function transcriptionPendingToastId(interviewId: number): string {
  return `transcription-pending-${interviewId}`
}

function triggerTextFileDownload(text: string, filename: string): void {
  try {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    /* ограничения окружения — без alert */
  }
}

interface TranscriptionCellProps {
  interviewId: number
  /** Статус из списка API: none | pending | processing | completed | failed */
  initialStatus: string
  /** Сообщение об ошибке из списка при failed (сериализатор). */
  initialErrorMessage?: string
  /** Менеджер и HR/outstaff — просмотр и поллинг, без запуска/повтора из SPA. */
  allowStartTranscription: boolean
}

/**
 * Запуск транскрибации (админ) и просмотр текста в модальном окне скачиванием TXT.
 */
function TranscriptionCell({
  interviewId,
  initialStatus,
  initialErrorMessage = '',
  allowStartTranscription,
}: TranscriptionCellProps) {
  const queryClient = useQueryClient()
  const titleId = useId()
  const [textOpen, setTextOpen] = useState(false)
  const [baseStatus, setBaseStatus] = useState(initialStatus)
  const onTextModalExit = useCallback(() => setTextOpen(false), [])
  const textModal = useModalEnterExit(textOpen, { onExitComplete: onTextModalExit })
  const pollPrevStatusRef = useRef<string | undefined>(undefined)

  const { shouldMount: textModalMounted, requestClose: closeTextModal } = textModal

  useBodyScrollLock(textModalMounted)

  useEffect(() => {
    if (!textModalMounted) {
      return
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeTextModal()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [textModalMounted, closeTextModal])

  const pollingWanted = baseStatus === 'pending' || baseStatus === 'processing'

  const statusQuery = useQuery({
    queryKey: ['transcription-status', interviewId],
    queryFn: () => getTranscriptionStatus(interviewId),
    enabled: pollingWanted,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      if (s === 'pending' || s === 'processing') {
        return 2000
      }
      return false
    },
  })

  const polled = statusQuery.data?.status
  const effectiveStatus = pollingWanted && polled ? polled : baseStatus

  useEffect(() => {
    const d = statusQuery.data
    if (!d?.status) {
      return
    }
    const prev = pollPrevStatusRef.current
    const cur = d.status
    if (prev === cur) {
      return
    }
    pollPrevStatusRef.current = cur

    if (cur === 'failed') {
      const em = (d.error_message ?? '').trim()
      toast.dismiss(transcriptionPendingToastId(interviewId))
      toast.error(
        em
          ? `❌ Ошибка транскрипции #${interviewId}: ${em}`
          : `❌ Ошибка транскрипции #${interviewId}`,
        { id: `transcription-error-${interviewId}` },
      )
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
    } else if (cur === 'completed' && prev !== undefined && prev !== 'completed') {
      toast.dismiss(transcriptionPendingToastId(interviewId))
      toast.success(`✅ Транскрипция собеседования #${interviewId} завершена`)
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
    }
  }, [statusQuery.data, interviewId, queryClient])

  const transcribeMutation = useMutation({
    mutationFn: () => postTranscribe(interviewId),
    onSuccess: (data) => {
      if (data.error) {
        toast.dismiss(transcriptionPendingToastId(interviewId))
        toast.error(data.error)
        return
      }
      const serverMsg = (data.message ?? '').trim()
      if (serverMsg === 'Уже в очереди') {
        toast.info(`Транскрипция собеседования #${interviewId} уже в очереди`, {
          id: transcriptionPendingToastId(interviewId),
          duration: 6000,
        })
      } else {
        toast.warning(`🎙️ Транскрипция собеседования #${interviewId} запущена…`, {
          id: transcriptionPendingToastId(interviewId),
          duration: Number.POSITIVE_INFINITY,
          closeButton: false,
        })
      }
      setBaseStatus('pending')
      void queryClient.invalidateQueries({ queryKey: ['transcription-status', interviewId] })
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
    },
    onError: (err: unknown) => {
      toast.dismiss(transcriptionPendingToastId(interviewId))
      const ax = err as { response?: { data?: { error?: string; detail?: string } } }
      const msg =
        ax.response?.data?.error ??
        ax.response?.data?.detail ??
        'Не удалось запустить транскрипцию'
      toast.error(String(msg))
    },
  })

  const textQuery = useQuery({
    queryKey: ['transcription-text', interviewId],
    queryFn: async () => {
      try {
        return await getTranscriptionText(interviewId)
      } catch (e: unknown) {
        const ax = e as { response?: { status?: number; data?: { error?: string } } }
        if (ax.response?.status === 404) {
          return { error: ax.response.data?.error ?? 'Ещё не готово' }
        }
        throw e
      }
    },
    enabled: textOpen,
  })

  const errMsg =
    (statusQuery.data?.error_message ?? '').trim() || (initialErrorMessage ?? '').trim() || undefined

  const onButtonClick = () => {
    if (effectiveStatus === 'completed') {
      setTextOpen(true)
      return
    }
    if (!allowStartTranscription) {
      return
    }
    if (effectiveStatus === 'failed' || effectiveStatus === 'none') {
      transcribeMutation.mutate()
    }
  }

  let btnClass = 'btn-outline-primary btn-small interview-tr-btn interviews-action-emoji'
  let title = 'Транскрибировать'
  let disabled = transcribeMutation.isPending

  if (effectiveStatus === 'completed') {
    btnClass = 'btn-success btn-small interview-tr-btn interviews-action-emoji'
    title = 'Транскрипция готова — нажмите для просмотра'
    disabled = false
  } else if (effectiveStatus === 'failed') {
    btnClass = 'btn-danger btn-small interview-tr-btn interviews-action-emoji'
    title = errMsg
      ? `Ошибка: ${errMsg} — нажмите для повтора`
      : 'Ошибка транскрипции — нажмите для повтора'
    if (!allowStartTranscription) {
      title = errMsg ? `Ошибка транскрипции: ${errMsg}` : 'Ошибка транскрипции'
      disabled = true
    }
  } else if (effectiveStatus === 'pending' || effectiveStatus === 'processing') {
    btnClass = 'btn-warning btn-small interview-tr-btn interview-tr-btn--pulse interviews-action-emoji'
    title = 'Транскрипция выполняется…'
    disabled = true
  } else if (!allowStartTranscription) {
    title = 'Запуск транскрипции доступен администратору'
    disabled = true
  }

  const textPayload = textQuery.data
  const downloadFilename =
    textPayload?.filename?.trim() || `Транскрипция_${interviewId}.txt`
  const canDownloadTxt =
    Boolean(textPayload?.text && String(textPayload.text).length > 0) && !textPayload?.error

  return (
    <>
      <span
        className="transcription-btn-wrap"
        data-pk={String(interviewId)}
        data-status={effectiveStatus}
      >
        <button
          type="button"
          className={btnClass}
          title={title}
          aria-label={title}
          disabled={disabled}
          onClick={onButtonClick}
        >
          🎙️
        </button>
      </span>
      {textModalMounted
        ? createPortal(
            <div
              className={`transcription-modal-overlay ${textModal.overlayOpenClass}`}
              role="presentation"
              onClick={() => closeTextModal()}
            >
              <div
                className="transcription-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby={titleId}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="transcription-modal-header">
                  <h2 className="transcription-modal-title" id={titleId}>
                    Транскрипция собеседования #{interviewId}
                  </h2>
                  <div className="transcription-modal-header-actions">
                    <button
                      type="button"
                      className="btn-primary transcription-modal-download-btn"
                      disabled={!canDownloadTxt}
                      title={
                        canDownloadTxt
                          ? `Скачать полный текст в UTF-8 (${downloadFilename})`
                          : 'Доступно после загрузки текста транскрипции'
                      }
                      onClick={() => {
                        if (textPayload?.text) {
                          triggerTextFileDownload(textPayload.text, downloadFilename)
                        }
                      }}
                    >
                      Скачать TXT-файл с транскрибацией
                    </button>
                    <button
                      type="button"
                      className="transcription-modal-close"
                      aria-label="Закрыть"
                      onClick={() => closeTextModal()}
                    >
                      ×
                    </button>
                  </div>
                </div>
                <div className="transcription-modal-inner">
                  {textQuery.isLoading ? <p className="transcription-modal-status">Загрузка…</p> : null}
                  {textPayload?.error ? (
                    <p className="form-error transcription-modal-status">{textPayload.error}</p>
                  ) : null}
                  {textPayload?.text ? (
                    <pre className="transcription-modal-body">{textPayload.text}</pre>
                  ) : null}
                </div>
                <div className="transcription-modal-footer">
                  <button type="button" className="btn-secondary" onClick={() => closeTextModal()}>
                    Закрыть
                  </button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  )
}

export default TranscriptionCell
