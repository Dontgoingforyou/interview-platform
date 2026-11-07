import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadInternPortalVideo } from '../../api/internsPortalApi'
import VideoUploadModal, { type VideoUploadModalPhase } from '../../components/internsPortal/VideoUploadModal'
import Pagination from '../../components/Pagination'
import { InlineError, ListPageSkeleton, LoadingLine } from '../../components/ui'
import { INTERN_PORTAL_MAX_VIDEO_BYTES } from '../../constants/internsPortal'
import { useInternPortalList } from '../../hooks/internsPortal/useInternPortalList'
import { useInternPortalUploadTaskPolling } from '../../hooks/internsPortal/useInternPortalUploadTaskPolling'
import type { InternPortalInterviewRow } from '../../types/internsPortal'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { internPortalUploadErrorMessage } from '../../utils/internsPortal/uploadErrors'
import { toast } from '../../utils/toast'

function formatPortalDate(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const [y, m, d] = iso.split('-')
  if (!y || !m || !d) {
    return iso
  }
  return `${d}.${m}.${y}`
}

function formatPortalTime(t: string | null): string {
  if (!t) {
    return '—'
  }
  const parts = t.split(':')
  if (parts.length >= 2) {
    return `${parts[0]}:${parts[1]}`
  }
  return t
}

function InternsPortalPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10) || 1)

  const listQuery = useInternPortalList(page, {
    refetchInterval: (q) => {
      const rows = q.state.data?.results ?? []
      const hasActive = rows.some((r) => r.upload_task_id)
      return hasActive ? 3000 : false
    },
  })

  const count = listQuery.data?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / 20))
  const results = listQuery.data?.results ?? []

  const hasActiveUploads = results.some((r) => r.upload_task_id)

  const uploadProgressByInterviewId = useInternPortalUploadTaskPolling(results, queryClient)

  const [modalOpen, setModalOpen] = useState(false)
  const [modalInterviewId, setModalInterviewId] = useState<number | null>(null)
  const [modalLabel, setModalLabel] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<VideoUploadModalPhase>('pick')
  const [uploadPercent, setUploadPercent] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const resetModal = useCallback(() => {
    setModalOpen(false)
    setModalInterviewId(null)
    setModalLabel('')
    setFile(null)
    setPhase('pick')
    setUploadPercent(0)
    setErrorMessage(null)
  }, [])

  const handleModalExitComplete = useCallback(() => {
    setModalOpen(false)
    setFile(null)
    setPhase('pick')
    setUploadPercent(0)
    setErrorMessage(null)
    setModalInterviewId(null)
    setModalLabel('')
  }, [])

  const uploadMutation = useMutation({
    mutationFn: ({ id, f }: { id: number; f: File }) =>
      uploadInternPortalVideo(id, f, setUploadPercent),
    onSuccess: () => {
      // Закрываем модалку сразу после получения task_id с сервера.
      // Прогресс (upload_task_id) будет виден в строке таблицы через refetchInterval.
      resetModal()
      void queryClient.invalidateQueries({ queryKey: ['interns-portal', 'interviews'] })
    },
    onError: (error) => {
      setPhase('error')
      setUploadPercent(0)
      const msg = internPortalUploadErrorMessage(error)
      setErrorMessage(msg)
      toast.error(msg)
    },
  })

  function openUploadModal(row: InternPortalInterviewRow) {
    const label = `#${row.id} — ${row.interview_type_display}${row.date ? ` (${formatPortalDate(row.date)})` : ''}`
    setModalInterviewId(row.id)
    setModalLabel(label)
    setFile(null)
    setPhase('pick')
    setUploadPercent(0)
    setErrorMessage(null)
    setModalOpen(true)
  }

  function onPageChange(next: number) {
    const nextParams = new URLSearchParams(searchParams)
    if (next <= 1) {
      nextParams.delete('page')
    } else {
      nextParams.set('page', String(next))
    }
    setSearchParams(nextParams, { replace: true })
  }

  function handleSubmitUpload() {
    if (!modalInterviewId || !file) {
      return
    }
    if (file.size > INTERN_PORTAL_MAX_VIDEO_BYTES) {
      toast.error('Файл больше 10 ГБ')
      return
    }
    setPhase('uploading')
    setUploadPercent(0)
    uploadMutation.mutate({ id: modalInterviewId, f: file })
  }

  function renderLinkCell(row: InternPortalInterviewRow) {
    const { url, label } = row.interview_display
    if (url) {
      return (
        <a href={url} target="_blank" rel="noopener noreferrer">
          {label || 'Ссылка'}
        </a>
      )
    }
    if (label) {
      return <span className="text-muted">{label}</span>
    }
    return <span className="text-muted">—</span>
  }

  function renderStatusCell(row: InternPortalInterviewRow) {
    if (row.upload_action_state === 'video') {
      return <span className="upload-status upload-status--done">ЗАГРУЖЕН</span>
    }
    if (row.upload_action_state === 'uploading') {
      const live = uploadProgressByInterviewId[row.id]
      if (live?.error) {
        return <span className="upload-status upload-status--error">{live.error}</span>
      }
      const pct = live?.percent ?? 0
      const statusText = live?.statusText ?? 'Загрузка в облако…'
      return (
        <div className="portal-table__progress-wrap">
          <p className="portal-table__progress-status">{statusText}</p>
          <div className="portal-table__progress-track">
            <div className="portal-table__progress-bar" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )
    }
    if (row.upload_action_state === 'office' || row.upload_action_state === 'phone') {
      return <span className="text-muted">—</span>
    }
    return <span className="upload-status upload-status--needed">НАДО ЗАГРУЗИТЬ</span>
  }

  const portalSkeletonHead = (
    <thead>
      <tr>
        <th>ID</th>
        <th>ФИО</th>
        <th>Направление</th>
        <th>Компания</th>
        <th>Тип</th>
        <th>Дата</th>
        <th>Время</th>
        <th>Статус загрузки</th>
        <th>Ссылка на созвон</th>
        <th>Вакансия</th>
        <th>Собеседование</th>
      </tr>
    </thead>
  )

  function renderActionCell(row: InternPortalInterviewRow) {
    if (row.upload_action_state === 'video' && row.upload_action_url) {
      return (
        <a
          href={row.upload_action_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary btn-upload-row"
        >
          Смотреть запись
        </a>
      )
    }
    if (row.upload_action_state === 'uploading') {
      return (
        <span className="btn-secondary btn-upload-row" aria-busy="true">
          Загрузка…
        </span>
      )
    }
    if (row.upload_action_state === 'office' || row.upload_action_state === 'phone') {
      return <span className="text-muted">—</span>
    }
    if (row.needs_student_video_upload) {
      return (
        <button
          type="button"
          className="btn-primary btn-upload-row"
          onClick={() => openUploadModal(row)}
        >
          Загрузить
        </button>
      )
    }
    return <span className="text-muted">—</span>
  }

  return (
    <>
      <div className="portal-header">
        <h2 className="portal-header__title">Мои собеседования</h2>
      </div>

      {listQuery.isLoading ? (
        <div className="portal-table-wrap">
          <ListPageSkeleton
            colCount={11}
            tableHead={portalSkeletonHead}
            metricCardsCount={0}
            dataTableClassName="table portal-table"
          />
        </div>
      ) : null}
      {listQuery.isFetching && listQuery.data && !hasActiveUploads ? <LoadingLine message="Обновление списка…" /> : null}
      {listQuery.isError ? <InlineError message="Не удалось загрузить собеседования." /> : null}

      {!listQuery.isLoading && results.length === 0 ? (
        <p className="text-muted">
          Собеседования не найдены. Обратитесь к менеджеру, если это ошибка.
        </p>
      ) : null}

      {results.length > 0 ? (
        <div
          className={withListDataRefreshingClass(
            'intern-portal-list-data',
            !hasActiveUploads && isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
          )}
        >
          <div className="portal-table-wrap">
            <table className="table portal-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>ФИО</th>
                  <th>Направление</th>
                  <th>Компания</th>
                  <th>Тип</th>
                  <th>Дата</th>
                  <th>Время</th>
                  <th>Статус загрузки</th>
                  <th>Ссылка на созвон</th>
                  <th>Вакансия</th>
                  <th>Собеседование</th>
                </tr>
              </thead>
              <tbody>
                {results.map((row) => (
                  <tr key={row.id} className={row.upload_action_state === 'uploading' ? 'row-uploading' : ''}>
                    <td>{row.id}</td>
                    <td>{row.intern_full_name}</td>
                    <td>{row.direction_name ?? '—'}</td>
                    <td>{row.company_name ?? '—'}</td>
                    <td>{row.interview_type_display}</td>
                    <td>{formatPortalDate(row.date)}</td>
                    <td>{formatPortalTime(row.time)}</td>
                    <td className="portal-table__status-cell">{renderStatusCell(row)}</td>
                    <td className="portal-table__upload-cell">{renderActionCell(row)}</td>
                    <td>
                      {row.vacancy_link && row.vacancy_link.toLowerCase().startsWith('http') ? (
                        <a href={row.vacancy_link} target="_blank" rel="noopener noreferrer">
                          Ссылка
                        </a>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>{renderLinkCell(row)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={onPageChange}
            showPageInput
          />
        </div>
      ) : null}

      <VideoUploadModal
        open={modalOpen}
        interviewLabel={modalLabel}
        interviewId={modalInterviewId}
        file={file}
        onFileChange={setFile}
        onExitComplete={handleModalExitComplete}
        onSubmit={handleSubmitUpload}
        phase={phase}
        uploadPercent={uploadPercent}
        errorMessage={errorMessage}
      />
    </>
  )
}

export default InternsPortalPage
