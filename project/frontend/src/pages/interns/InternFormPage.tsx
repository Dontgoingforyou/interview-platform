import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import type { SingleValue } from 'react-select'

import { createIntern, getIntern, updateIntern } from '../../api/internsApi'
import { getDirections, getManagersForFilters } from '../../api/referenceApi'
import InternFormFields from '../../components/interns/form/InternFormFields'
import {
  INTERN_MANUAL_STATUS_FORM_OPTIONS,
  INTERN_TRAINING_OPTIONS,
} from '../../constants/internStatuses'
import { useSessionFormDraft } from '../../hooks/useSessionFormDraft'
import { useAuthStore } from '../../store/authStore'
import { canWriteInterviews, isAdminUser } from '../../utils/authRoles'
import type { InternWritePayload } from '../../types/intern'
import type { SelectOption } from '../../types/common'
import { toast } from '../../utils/toast'

/**
 * Создание / редактирование студента.
 * Поля формы — в components/interns/form/InternFormFields.tsx.
 */
export default function InternFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const internId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const canManageInterns = canWriteInterviews(user)

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<Partial<InternWritePayload>>({
    type_of_training: 'internal',
    hiring_hr: '',
    responsible_hr: '',
    group: '',
  })

  const { clearDraft } = useSessionFormDraft({
    storageKey: 'react-intern-form-draft-v1',
    form: form as unknown as Record<string, unknown>,
    setForm: setForm as Dispatch<SetStateAction<Record<string, unknown>>>,
    enabled: !isEdit,
  })

  const detailQuery = useQuery({
    queryKey: ['intern', internId],
    queryFn: () => getIntern(internId),
    enabled: isEdit && !Number.isNaN(internId),
  })

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const managersQuery = useQuery({
    queryKey: ['managers-for-filters'],
    queryFn: getManagersForFilters,
    staleTime: 300_000,
  })

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация формы из API */
  useEffect(() => {
    const row = detailQuery.data
    if (!row) {
      return
    }
    setForm({
      full_name: row.full_name,
      email: row.email ?? '',
      telegram_username: row.telegram_username ?? '',
      direction_id: row.direction_id,
      cv: row.cv ?? '',
      date_of_receipt: row.date_of_receipt ?? '',
      date_of_birth: row.date_of_birth ?? '',
      hiring_hr: row.hiring_hr,
      responsible_hr: row.responsible_hr,
      group: row.group,
      type_of_training: row.type_of_training,
      legend: row.legend ?? '',
      hr_feedback: row.hr_feedback ?? '',
      mentor_feedback: row.mentor_feedback ?? '',
      real_interview_date: row.real_interview_date ?? '',
      manual_status: row.manual_status ?? '',
      manager_email: row.manager_email ?? '',
    })
  }, [detailQuery.data])
  /* eslint-enable react-hooks/set-state-in-effect */

  const lockedManagerEmail = !isEdit && !isAdmin ? user?.email : undefined

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: InternWritePayload = {
        full_name: form.full_name!.trim(),
        email: form.email?.trim() || null,
        telegram_username: form.telegram_username?.trim() || null,
        direction_id: form.direction_id!,
        cv: form.cv?.trim() || null,
        date_of_receipt: form.date_of_receipt?.trim() || null,
        date_of_birth: form.date_of_birth?.trim() || null,
        hiring_hr: form.hiring_hr!.trim(),
        responsible_hr: form.responsible_hr!.trim(),
        group: form.group!.trim(),
        type_of_training: form.type_of_training!,
        legend: form.legend?.trim() || null,
        hr_feedback: form.hr_feedback?.trim() || null,
        mentor_feedback: form.mentor_feedback?.trim() || null,
        real_interview_date: form.real_interview_date?.trim() || null,
        manual_status: form.manual_status?.trim() || null,
        manager_email: (lockedManagerEmail ?? form.manager_email)?.trim() || null,
      }
      if (isEdit) {
        return updateIntern(internId, payload)
      }
      return createIntern(payload)
    },
    onSuccess: () => {
      if (!isEdit) {
        clearDraft()
      }
      toast.success(isEdit ? 'Студент обновлён' : 'Студент добавлен')
      void queryClient.invalidateQueries({ queryKey: ['interns'] })
      navigate('/interns')
    },
    onError: (err: unknown) => {
      if (import.meta.env.DEV) console.error('Ошибка сохранения студента:', err)
      const ax = err as { response?: { data?: Record<string, string[] | string> } }
      const data = ax.response?.data
      if (!data || typeof data !== 'object') {
        toast.error('Не удалось сохранить студента')
        return
      }
      const next: Record<string, string> = {}
      let detailMsg: string | null = null
      for (const [k, v] of Object.entries(data)) {
        if (k === 'detail') {
          if (Array.isArray(v)) {
            detailMsg = v.join(' ')
          } else if (typeof v === 'string') {
            detailMsg = v
          }
        } else if (Array.isArray(v)) {
          next[k] = v.join(' ')
        } else if (typeof v === 'string') {
          next[k] = v
        }
      }
      setFieldErrors(next)
      if (Object.keys(next).length > 0) {
        toast.error(detailMsg ?? 'Проверьте поля формы')
      } else if (detailMsg) {
        toast.error(detailMsg)
      } else {
        toast.error('Не удалось сохранить студента')
      }
    },
  })

  const directionOptions = useMemo<SelectOption<number>[]>(
    () => (directionsQuery.data ?? []).map((d) => ({ value: d.id, label: d.name })),
    [directionsQuery.data],
  )

  const managerOptions = useMemo<SelectOption[]>(
    () => (managersQuery.data ?? []).map((m) => ({ value: m.email, label: m.full_name || m.email })),
    [managersQuery.data],
  )

  const directionValue = useMemo((): SingleValue<SelectOption<number>> => {
    const did = form.direction_id
    if (did == null) {
      return null
    }
    return directionOptions.find((o) => o.value === did) ?? null
  }, [form.direction_id, directionOptions])

  const managerValue = useMemo((): SingleValue<SelectOption> => {
    const em = lockedManagerEmail ?? form.manager_email
    if (!em) {
      return null
    }
    return managerOptions.find((o) => o.value === em) ?? { value: em, label: em }
  }, [lockedManagerEmail, form.manager_email, managerOptions])

  const trainingValue =
    INTERN_TRAINING_OPTIONS.find((o) => o.value === form.type_of_training) ?? INTERN_TRAINING_OPTIONS[0]

  const manualStatusValue =
    INTERN_MANUAL_STATUS_FORM_OPTIONS.find((o) => o.value === (form.manual_status ?? '')) ??
    INTERN_MANUAL_STATUS_FORM_OPTIONS[0]

  if (!canManageInterns) {
    return <Navigate to="/interns" replace />
  }

  if (isEdit && !isAdmin) {
    return <Navigate to="/interns" replace />
  }

  if (isEdit && (Number.isNaN(internId) || detailQuery.isError)) {
    return (
      <div>
        <p className="form-error">Студент не найден.</p>
        <Link className="btn-secondary" to="/interns">
          К списку
        </Link>
      </div>
    )
  }

  if (isEdit && detailQuery.isLoading) {
    return <p>Загрузка…</p>
  }

  return (
    <div>
      <h1 className="page-title">{isEdit ? `Студент #${id}` : 'Новый студент'}</h1>
      <div className="interview-form-back-row">
        <Link className="btn-secondary" to="/interns">
          ← К списку
        </Link>
      </div>

      <InternFormFields
        form={form}
        setForm={setForm}
        fieldErrors={fieldErrors}
        directionOptions={directionOptions}
        managerOptions={managerOptions}
        directionValue={directionValue}
        managerValue={managerValue}
        trainingValue={trainingValue}
        manualStatusValue={manualStatusValue}
        managerSelectLocked={!isAdmin && !isEdit}
        directionsLoading={directionsQuery.isLoading}
        managersLoading={managersQuery.isLoading}
        savePending={saveMutation.isPending}
        onSubmit={(e) => {
          e.preventDefault()
          setFieldErrors({})
          saveMutation.mutate()
        }}
      />
    </div>
  )
}
