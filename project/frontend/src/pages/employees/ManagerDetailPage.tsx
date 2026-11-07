import { useCallback, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import EmployeeAbsenceModal from '../../components/employees/board/EmployeeAbsenceModal'
import EmployeeInternTable from '../../components/employees/board/EmployeeInternTable'
import EmployeeMonthTables from '../../components/employees/board/EmployeeMonthTables'
import { InlineError } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import PageIntroCard from '../../components/ui/PageIntroCard'
import { upsertWeeklyStatus } from '../../api/employeesApi'
import { patchInternManualStatus } from '../../api/internsApi'
import { ABSENCE_STATUS_OPTIONS } from '../../constants/absenceStatuses'
import { managerBoardQueryKey, useManagerBoard } from '../../hooks/employees/useManagerBoard'
import { useAuthStore } from '../../store/authStore'
import { canWriteInterviews, emailsEqualIgnoreCase, isAdminUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'
import type { BoardAbsenceInfo } from '../../types/employee'

interface AbsenceTarget {
  internId: number
  weekStart: string
  info: BoardAbsenceInfo | null
}

export default function ManagerDetailPage() {
  const { managerEmail } = useParams<{ managerEmail: string }>()
  const email = managerEmail?.trim() ? decodeURIComponent(managerEmail) : ''
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const boardQuery = useManagerBoard(email || undefined)

  const [showAllWeeks, setShowAllWeeks] = useState(false)
  const [absenceTarget, setAbsenceTarget] = useState<AbsenceTarget | null>(null)
  const [statusSavedFlashInternId, setStatusSavedFlashInternId] = useState<number | null>(null)
  const statusFlashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const invalidateBoard = useCallback(() => {
    if (email) {
      void qc.invalidateQueries({ queryKey: managerBoardQueryKey(email) })
    }
  }, [email, qc])

  const statusMutation = useMutation({
    mutationFn: ({ internId, manual_status }: { internId: number; manual_status: string }) =>
      patchInternManualStatus(internId, manual_status),
    onSuccess: (_data, variables) => {
      invalidateBoard()
      toast.success('Статус обновлён')
      if (statusFlashTimerRef.current) {
        clearTimeout(statusFlashTimerRef.current)
      }
      setStatusSavedFlashInternId(variables.internId)
      statusFlashTimerRef.current = setTimeout(() => {
        setStatusSavedFlashInternId(null)
        statusFlashTimerRef.current = null
      }, 700)
    },
    onError: () => toast.error('Не удалось обновить статус'),
  })

  const weeklyMutation = useMutation({
    mutationFn: (payload: Parameters<typeof upsertWeeklyStatus>[0]) => upsertWeeklyStatus(payload),
    onSuccess: () => {
      invalidateBoard()
      toast.success('Сохранено')
    },
    onError: () => toast.error('Не удалось сохранить неделю'),
  })

  const handleStatusChange = useCallback(
    (internId: number, value: string) => {
      const b = boardQuery.data
      if (!b) {
        return
      }
      const row =
        b.active_interns.find((r) => r.intern.id === internId) ??
        b.inactive_interns.find((r) => r.intern.id === internId) ??
        b.all_interns.find((r) => r.intern.id === internId)
      if (row?.status === value) {
        return
      }
      statusMutation.mutate({ internId, manual_status: value })
    },
    [boardQuery.data, statusMutation],
  )

  const handleSaveAdminCount = useCallback(
    async (internId: number, weekStart: string, value: number | null) => {
      await weeklyMutation.mutateAsync({
        intern: internId,
        week_start: weekStart,
        manual_interview_count: value,
      })
    },
    [weeklyMutation],
  )

  const handleAbsenceSave = useCallback(
    async (status: string, notes: string) => {
      if (!absenceTarget) {
        return
      }
      await weeklyMutation.mutateAsync({
        intern: absenceTarget.internId,
        week_start: absenceTarget.weekStart,
        absence_status: status,
        absence_notes: notes,
      })
    },
    [absenceTarget, weeklyMutation],
  )

  const handleAbsenceRemove = useCallback(async () => {
    if (!absenceTarget) {
      return
    }
    await weeklyMutation.mutateAsync({
      intern: absenceTarget.internId,
      week_start: absenceTarget.weekStart,
      absence_status: null,
      absence_notes: '',
    })
  }, [absenceTarget, weeklyMutation])

  if (!email) {
    return <InlineError message="Не указан менеджер." />
  }

  if (boardQuery.isLoading) {
    return <LoadingLine message="Загрузка доски…" />
  }

  if (boardQuery.isError) {
    return (
      <div>
        <InlineError message="Не удалось загрузить данные." />
        <Link to="/employees" className="btn-secondary">
          ← К списку
        </Link>
      </div>
    )
  }

  const board = boardQuery.data!

  // Согласовано с canWriteInterviews: двойное членство hrs + employment не отнимает запись у менеджера.
  const canWrite =
    isAdmin || (canWriteInterviews(user) && emailsEqualIgnoreCase(user?.email, board.manager.email))

  return (
    <div className="page-employees-detail">
      <PageIntroCard title={`Сотрудники менеджера: ${board.manager.full_name}`}>
        <p>Таблица сотрудников, назначенных на этого менеджера. Показаны последние 6 недель собеседований.</p>
      </PageIntroCard>
      <Link to="/employees" className="btn-secondary employee-detail-back-btn">
        ← К списку
      </Link>

      <EmployeeInternTable
        title="Активные сотрудники"
        recentWeeks={board.recent_weeks}
        rows={board.active_interns}
        directionsDict={board.directions_dict}
        coefficients={board.coefficients}
        isAdmin={isAdmin}
        canWrite={canWrite}
        statusPending={statusMutation.isPending}
        onStatusChange={handleStatusChange}
        onOpenAbsence={setAbsenceTarget}
        onSaveAdminCount={handleSaveAdminCount}
        statusSavedFlashInternId={statusSavedFlashInternId}
      />

      {board.inactive_interns.length > 0 ? (
        <EmployeeInternTable
          title="Неактивные сотрудники"
          recentWeeks={board.recent_weeks}
          rows={board.inactive_interns}
          directionsDict={board.directions_dict}
          coefficients={null}
          isAdmin={isAdmin}
          canWrite={canWrite}
          statusPending={statusMutation.isPending}
          onStatusChange={handleStatusChange}
          onOpenAbsence={setAbsenceTarget}
          onSaveAdminCount={handleSaveAdminCount}
          statusSavedFlashInternId={statusSavedFlashInternId}
        />
      ) : null}

      <button type="button" className="toggle-button" onClick={() => setShowAllWeeks((v) => !v)}>
        {showAllWeeks ? 'Скрыть все недели' : 'Показать все недели'}
      </button>

      {showAllWeeks ? (
        <div className="all-weeks-container">
          <EmployeeMonthTables
            board={board}
            isAdmin={isAdmin}
            canWrite={canWrite}
            statusPending={statusMutation.isPending}
            onStatusChange={handleStatusChange}
            onOpenAbsence={setAbsenceTarget}
            onSaveAdminCount={handleSaveAdminCount}
            statusSavedFlashInternId={statusSavedFlashInternId}
          />
        </div>
      ) : null}

      <EmployeeAbsenceModal
        open={absenceTarget != null}
        initialStatus={absenceTarget?.info?.status ?? ABSENCE_STATUS_OPTIONS[0].value}
        initialNotes={absenceTarget?.info?.notes ?? ''}
        onExitComplete={() => setAbsenceTarget(null)}
        onSave={handleAbsenceSave}
        onRemove={handleAbsenceRemove}
      />
    </div>
  )
}
