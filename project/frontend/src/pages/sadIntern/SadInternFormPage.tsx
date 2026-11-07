import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useCallback, useEffect, useMemo, useState } from 'react'
import AsyncSelect from 'react-select/async'
import Select from 'react-select'
import type { SingleValue } from 'react-select'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'

import { createSadIntern, getSadIntern, updateSadIntern } from '../../api/sadInternApi'
import { getIntern } from '../../api/internsApi'
import { getManagersForFilters } from '../../api/referenceApi'
import { useInternAsyncSelectMinQuery } from '../../hooks/useInternAsyncSelectMinQuery'
import { InlineError, LoadingLine } from '../../components/ui'
import { SAD_INTERN_STATUS_OPTIONS } from '../../constants/sadInternStatuses'
import { useAuthStore } from '../../store/authStore'
import type { SelectOption } from '../../types/common'
import type { InternAsyncSelectOption } from '../../utils/interns/internAsyncSelectOptions'
import type { SadInternWritePayload } from '../../types/sadIntern'
import { isAdminUser, isHrOrOutstaffUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'

/**
 * Создание и редактирование записи в списке «грустят».
 */
export default function SadInternFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const sadId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [internValue, setInternValue] = useState<SingleValue<InternAsyncSelectOption>>(null)
  const [waitingSince, setWaitingSince] = useState('')
  const [telegramUsername, setTelegramUsername] = useState('')
  const [managerEmail, setManagerEmail] = useState('')
  const [status, setStatus] = useState('')
  const [note, setNote] = useState('')

  const detailQuery = useQuery({
    queryKey: ['sad-intern', 'detail', sadId],
    queryFn: () => getSadIntern(sadId),
    enabled: isEdit && !Number.isNaN(sadId),
  })

  const managersQuery = useQuery({
    queryKey: ['managers-for-filters'],
    queryFn: getManagersForFilters,
    enabled: isAdmin,
    staleTime: 300_000,
  })

  const managerOptions: SelectOption<string>[] = useMemo(
    () =>
      (managersQuery.data ?? []).map((m) => ({
        value: m.email,
        label: m.full_name ? `${m.full_name} (${m.email})` : m.email,
      })),
    [managersQuery.data],
  )

  const managerSelectValue = useMemo(
    () => managerOptions.find((o) => o.value === managerEmail) ?? null,
    [managerOptions, managerEmail],
  )

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация из API */
  useEffect(() => {
    const row = detailQuery.data
    if (!row) {
      return
    }
    setInternValue({ value: row.intern, label: row.intern_name })
    setWaitingSince(row.waiting_since ? String(row.waiting_since).slice(0, 10) : '')
    setTelegramUsername(row.telegram_username ?? '')
    setManagerEmail(row.manager_email ?? '')
    setStatus(row.status ?? '')
    setNote(row.note ?? '')
  }, [detailQuery.data])
  /* eslint-enable react-hooks/set-state-in-effect */

  const loadInternOptions = useInternAsyncSelectMinQuery()

  const onInternChange = useCallback(
    async (opt: SingleValue<InternAsyncSelectOption>) => {
      setInternValue(opt)
      if (!opt || isEdit) {
        return
      }
      try {
        const data = await getIntern(opt.value)
        setTelegramUsername((prev) => prev || (data.telegram_username ?? ''))
        setWaitingSince((prev) => {
          if (prev) {
            return prev
          }
          const d = data.real_interview_date
          return d ? String(d).slice(0, 10) : ''
        })
      } catch {
        /* подсказки необязательны */
      }
    },
    [isEdit],
  )

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!internValue) {
        throw new Error('intern')
      }
      if (isEdit) {
        const patch: Partial<SadInternWritePayload> = {
          telegram_username: telegramUsername.trim() || null,
          status: status || null,
          note: note.trim() || null,
        }
        if (waitingSince) {
          patch.waiting_since = waitingSince
        }
        if (isAdmin) {
          patch.manager_email = managerEmail.trim() || null
        }
        return updateSadIntern(sadId, patch)
      }
      const createPayload: SadInternWritePayload = {
        intern: internValue.value,
        telegram_username: telegramUsername.trim() || null,
        status: status || null,
        note: note.trim() || null,
      }
      if (waitingSince) {
        createPayload.waiting_since = waitingSince
      }
      if (isAdmin && managerEmail.trim()) {
        createPayload.manager_email = managerEmail.trim()
      }
      return createSadIntern(createPayload)
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Запись обновлена' : 'Студент добавлен в список ожидания')
      void queryClient.invalidateQueries({ queryKey: ['sad-intern'] })
      navigate('/sad-intern')
    },
    onError: (err: unknown) => {
      if (import.meta.env.DEV) console.error(err)
      const ax = err as { response?: { data?: Record<string, string[] | string> }; message?: string }
      if (ax.message === 'intern') {
        setFieldErrors({ intern: 'Выберите студента' })
        toast.error('Выберите студента')
        return
      }
      const data = ax.response?.data
      if (data && typeof data === 'object') {
        const next: Record<string, string> = {}
        for (const [k, v] of Object.entries(data)) {
          next[k] = Array.isArray(v) ? v[0] : String(v)
        }
        setFieldErrors(next)
      }
      toast.error('Не удалось сохранить')
    },
  })

  if (!user || isHrOrOutstaffUser(user)) {
    return <Navigate to="/sad-intern" replace />
  }

  if (isEdit && Number.isNaN(sadId)) {
    return <Navigate to="/sad-intern" replace />
  }

  if (isEdit && detailQuery.isError && axios.isAxiosError(detailQuery.error)) {
    const s = detailQuery.error.response?.status
    if (s === 403 || s === 404) {
      return <Navigate to="/sad-intern" replace />
    }
  }

  const pageTitle = isEdit
    ? detailQuery.data?.intern_name
      ? `Редактирование: ${detailQuery.data.intern_name}`
      : 'Редактирование записи'
    : 'Новый «грустный» студент'

  return (
    <div className="page sad-intern-form-page">
      <h1 className="page-title">{pageTitle}</h1>
      <div className="interview-form-back-row">
        <Link to="/sad-intern" className="btn-secondary">
          ← К списку «грустят»
        </Link>
      </div>

      {isEdit && detailQuery.isLoading ? (
        <LoadingLine message="Загрузка записи…" />
      ) : null}
      {isEdit && detailQuery.isError && !axios.isAxiosError(detailQuery.error) ? (
        <InlineError message="Не удалось загрузить запись." />
      ) : null}

      {(!isEdit || detailQuery.data) && !(isEdit && detailQuery.isLoading) ? (
        <form
          className="interview-form"
          onSubmit={(e) => {
            e.preventDefault()
            setFieldErrors({})
            saveMutation.mutate()
          }}
        >
          <label htmlFor="sad-intern-form-intern">
            Студент *
            <AsyncSelect<InternAsyncSelectOption>
              inputId="sad-intern-form-intern"
              classNamePrefix="react-select"
              cacheOptions
              defaultOptions
              loadOptions={loadInternOptions}
              value={internValue}
              onChange={onInternChange}
              placeholder="Начните вводить ФИО (от 2 символов)…"
              isDisabled={isEdit}
            />
            {fieldErrors.intern ? <span className="form-error">{fieldErrors.intern}</span> : null}
          </label>

          <label htmlFor="sad-intern-waiting-since">
            Ждёт с (дата)
            <input
              id="sad-intern-waiting-since"
              type="date"
              className="form-input"
              value={waitingSince}
              onChange={(e) => setWaitingSince(e.target.value)}
            />
            <p className="muted form-hint">
              Если не указать, при создании подставится дата из карточки студента или сегодняшняя (как в веб-форме).
            </p>
            {fieldErrors.waiting_since ? <span className="form-error">{fieldErrors.waiting_since}</span> : null}
          </label>

          <label htmlFor="sad-intern-tg">
            Telegram (@username)
            <input
              id="sad-intern-tg"
              type="text"
              className="form-input"
              value={telegramUsername}
              onChange={(e) => setTelegramUsername(e.target.value)}
              placeholder="@username"
              autoComplete="off"
            />
            {fieldErrors.telegram_username ? (
              <span className="form-error">{fieldErrors.telegram_username}</span>
            ) : null}
          </label>

          {isAdmin ? (
            <label htmlFor="sad-intern-manager">
              Менеджер записи
              <Select<SelectOption<string>>
                inputId="sad-intern-manager"
                classNamePrefix="react-select"
                isClearable
                options={managerOptions}
                value={managerSelectValue}
                onChange={(opt) => setManagerEmail(opt?.value ?? '')}
                isLoading={managersQuery.isLoading}
                placeholder="По умолчанию — вы или менеджер студента"
              />
              {fieldErrors.manager_email ? (
                <span className="form-error">{fieldErrors.manager_email}</span>
              ) : null}
            </label>
          ) : null}

          <label htmlFor="sad-intern-status">
            Статус
            <select
              id="sad-intern-status"
              className="form-input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">—</option>
              {SAD_INTERN_STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {fieldErrors.status ? <span className="form-error">{fieldErrors.status}</span> : null}
          </label>

          <label htmlFor="sad-intern-note">
            Примечание
            <textarea
              id="sad-intern-note"
              className="form-input"
              rows={4}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            {fieldErrors.note ? <span className="form-error">{fieldErrors.note}</span> : null}
          </label>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Сохранение…' : 'Сохранить'}
            </button>
            <Link to="/sad-intern" className="btn-secondary">
              Отмена
            </Link>
          </div>
        </form>
      ) : null}
    </div>
  )
}
