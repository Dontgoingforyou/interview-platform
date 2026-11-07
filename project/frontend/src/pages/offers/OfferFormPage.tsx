import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import AsyncSelect from 'react-select/async'
import Select from 'react-select'
import type { SingleValue } from 'react-select'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'

import { createOffer, getOffer, updateOffer } from '../../api/offersApi'
import { getDirections } from '../../api/referenceApi'
import { useInternAsyncSelectMinQuery } from '../../hooks/useInternAsyncSelectMinQuery'
import { MONTH_CHOICES } from '../../constants/monthChoices'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import type { OfferWritePayload } from '../../types/offer'
import type { SelectOption } from '../../types/common'
import type { InternAsyncSelectOption } from '../../utils/interns/internAsyncSelectOptions'
import { toast } from '../../utils/toast'

const monthSelectOptions: SelectOption<number>[] = MONTH_CHOICES.map((m) => ({
  value: m.value,
  label: m.label,
}))

/**
 * Создание и редактирование оффера (только администратор).
 */
export default function OfferFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const offerId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const defaultYear = new Date().getFullYear()
  const defaultMonth = new Date().getMonth() + 1

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<Partial<OfferWritePayload>>(() =>
    isEdit ? {} : { month: defaultMonth, year: defaultYear },
  )
  const [internValue, setInternValue] = useState<SingleValue<InternAsyncSelectOption>>(null)

  const detailQuery = useQuery({
    queryKey: ['offer', offerId],
    queryFn: () => getOffer(offerId),
    enabled: isEdit && !Number.isNaN(offerId),
  })

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const directionOptions: SelectOption<number>[] = useMemo(
    () => (directionsQuery.data ?? []).map((d) => ({ value: d.id, label: d.name })),
    [directionsQuery.data],
  )

  const directionValue = useMemo(
    () => directionOptions.find((o) => o.value === form.direction_id) ?? null,
    [directionOptions, form.direction_id],
  )

  const monthValue = useMemo(
    () => monthSelectOptions.find((o) => o.value === form.month) ?? null,
    [form.month],
  )

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация из API */
  useEffect(() => {
    const row = detailQuery.data
    if (!row) {
      return
    }
    setForm({
      intern: row.intern,
      direction_id: row.direction_id ?? undefined,
      company: row.company ?? '',
      amount: row.amount ?? '',
      month: row.month,
      year: row.year,
    })
    setInternValue({
      value: row.intern,
      label: row.intern_name,
    })
  }, [detailQuery.data])
  /* eslint-enable react-hooks/set-state-in-effect */

  const loadInternOptions = useInternAsyncSelectMinQuery()

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!form.intern) {
        throw new Error('intern')
      }
      if (form.direction_id == null) {
        throw new Error('direction_id')
      }
      const company = form.company?.trim()
      if (!company) {
        throw new Error('company')
      }
      const month = form.month ?? defaultMonth
      const year = form.year ?? defaultYear
      const payload: OfferWritePayload = {
        intern: form.intern,
        direction_id: form.direction_id,
        company,
        amount: form.amount?.toString().trim() ? String(form.amount).trim() : null,
        month,
        year,
      }
      if (isEdit) {
        return updateOffer(offerId, payload)
      }
      return createOffer(payload)
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Оффер обновлён' : 'Оффер добавлен')
      void queryClient.invalidateQueries({ queryKey: ['offers'] })
      void queryClient.invalidateQueries({ queryKey: ['offer', offerId] })
      navigate('/offers')
    },
    onError: (err: unknown) => {
      if (import.meta.env.DEV) console.error(err)
      const ax = err as { response?: { data?: Record<string, string[] | string> }; message?: string }
      if (ax.message === 'intern') {
        setFieldErrors({ intern: 'Выберите студента' })
        return
      }
      if (ax.message === 'direction_id') {
        setFieldErrors({ direction_id: 'Выберите направление' })
        return
      }
      if (ax.message === 'company') {
        setFieldErrors({ company: 'Укажите компанию' })
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

  if (!isAdmin) {
    return <Navigate to="/offers" replace />
  }

  if (isEdit && Number.isNaN(offerId)) {
    return <Navigate to="/offers" replace />
  }

  const pageTitle = isEdit
    ? detailQuery.data?.intern_name
      ? `Редактирование оффера: ${detailQuery.data.intern_name}`
      : 'Редактирование оффера'
    : 'Новый оффер'

  return (
    <div className="page">
      <h1 className="page-title">{pageTitle}</h1>
      <div className="interview-form-back-row">
        <Link to="/offers" className="btn-secondary">
          ← К списку офферов
        </Link>
      </div>

      {isEdit && detailQuery.isLoading ? (
        <p className="muted">Загрузка…</p>
      ) : (
        <form
          className="interview-form"
          onSubmit={(e) => {
            e.preventDefault()
            setFieldErrors({})
            saveMutation.mutate()
          }}
        >
            <p className="interview-form-required-hint">Поля со звёздочкой (*) обязательны.</p>

            <label>
              Студент *
              <AsyncSelect<InternAsyncSelectOption>
                classNamePrefix="react-select"
                placeholder="Начните вводить ФИО…"
                loadingMessage={() => 'Загрузка…'}
                noOptionsMessage={() => 'Введите минимум 2 символа'}
                cacheOptions
                defaultOptions={false}
                isClearable
                loadOptions={loadInternOptions}
                value={internValue}
                onChange={(opt) => {
                  setInternValue(opt)
                  if (opt) {
                    setForm((f) => ({
                      ...f,
                      intern: opt.value,
                      direction_id: opt.directionId ?? f.direction_id,
                    }))
                  } else {
                    setForm((f) => ({ ...f, intern: undefined }))
                  }
                }}
              />
              {fieldErrors.intern ? <span className="form-error">{fieldErrors.intern}</span> : null}
            </label>

            <label>
              Направление *
              <Select<SelectOption<number>>
                classNamePrefix="react-select"
                isClearable
                isSearchable
                isLoading={directionsQuery.isLoading}
                options={directionOptions}
                value={directionValue}
                onChange={(opt) => setForm((f) => ({ ...f, direction_id: opt?.value }))}
              />
              {fieldErrors.direction_id ? (
                <span className="form-error">{fieldErrors.direction_id}</span>
              ) : null}
            </label>

            <label>
              Компания *
              <input
                className="form-input"
                placeholder="Название компании"
                value={form.company ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
              />
              {fieldErrors.company ? <span className="form-error">{fieldErrors.company}</span> : null}
            </label>

            <label>
              Сумма в оффере
              <input
                className="form-input"
                type="text"
                inputMode="decimal"
                placeholder="Необязательно"
                value={form.amount ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              />
              {fieldErrors.amount ? <span className="form-error">{fieldErrors.amount}</span> : null}
            </label>

            <label>
              Месяц *
              <Select<SelectOption<number>>
                classNamePrefix="react-select"
                options={monthSelectOptions}
                value={monthValue}
                onChange={(opt) =>
                  setForm((f) => ({ ...f, month: opt?.value ?? defaultMonth }))
                }
              />
              {fieldErrors.month ? <span className="form-error">{fieldErrors.month}</span> : null}
            </label>

            <label>
              Год *
              <input
                className="form-input"
                type="number"
                min={2000}
                max={2100}
                value={form.year ?? defaultYear}
                onChange={(e) => {
                  const y = parseInt(e.target.value, 10)
                  setForm((f) => ({ ...f, year: Number.isNaN(y) ? f.year : y }))
                }}
              />
              {fieldErrors.year ? <span className="form-error">{fieldErrors.year}</span> : null}
            </label>

            <div className="interview-form-actions">
              <button type="submit" className="btn-success" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? 'Сохранение…' : 'Сохранить'}
              </button>
              <Link to="/offers" className="btn-secondary">
                Отмена
              </Link>
            </div>
          </form>
      )}
    </div>
  )
}
