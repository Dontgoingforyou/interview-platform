import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import AsyncSelect from 'react-select/async'
import Select from 'react-select'
import type { SingleValue } from 'react-select'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'

import {
  addDebtPayment,
  createDebt,
  getDebt,
  updateDebt,
} from '../../api/debtsApi'
import { getDirections } from '../../api/referenceApi'
import { useInternAsyncSelectMinQuery } from '../../hooks/useInternAsyncSelectMinQuery'
import { ListPageFilterForm, TableScroll } from '../../components/ui'
import { DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { DEBT_PAYMENT_STATUS_OPTIONS } from '../../constants/debtChoices'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import type { DebtWritePayload } from '../../types/debt'
import type { SelectOption } from '../../types/common'
import type { InternAsyncSelectOption } from '../../utils/interns/internAsyncSelectOptions'
import { toast } from '../../utils/toast'

/**
 * Создание и редактирование долга (только администратор).
 */
export default function DebtFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const debtId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<Partial<DebtWritePayload>>({})
  const [internValue, setInternValue] = useState<SingleValue<InternAsyncSelectOption>>(null)
  const [payMonth, setPayMonth] = useState(1)
  const [payYear, setPayYear] = useState(new Date().getFullYear())
  const [payAmount, setPayAmount] = useState('')
  const [historyOpen, setHistoryOpen] = useState(false)
  const [addPaymentOpen, setAddPaymentOpen] = useState(false)

  const detailQuery = useQuery({
    queryKey: ['debt', debtId],
    queryFn: () => getDebt(debtId),
    enabled: isEdit && !Number.isNaN(debtId),
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

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация из API */
  useEffect(() => {
    const row = detailQuery.data
    if (!row) {
      return
    }
    setForm({
      intern: row.intern,
      direction_id: row.direction_id,
      telegram_username: row.telegram_username ?? '',
      email: row.email ?? '',
      total_amount: row.total_amount,
      paid_amount: row.paid_amount,
      payment_status: row.payment_status,
      act_date: row.act_date ?? '',
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
      const payload: DebtWritePayload = {
        intern: form.intern,
        direction_id: form.direction_id ?? null,
        telegram_username: form.telegram_username?.trim() || null,
        email: form.email?.trim() || null,
        total_amount: form.total_amount,
        paid_amount: form.paid_amount,
        payment_status: form.payment_status,
        act_date: form.act_date || null,
      }
      if (isEdit) {
        return updateDebt(debtId, payload)
      }
      return createDebt(payload)
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Запись о долге обновлена' : 'Запись о долге добавлена')
      void queryClient.invalidateQueries({ queryKey: ['debts'] })
      navigate('/debts')
    },
    onError: (err: unknown) => {
      if (import.meta.env.DEV) console.error(err)
      const ax = err as { response?: { data?: Record<string, string[] | string> }; message?: string }
      if (ax.message === 'intern') {
        setFieldErrors({ intern: 'Выберите студента' })
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

  const paymentMutation = useMutation({
    mutationFn: () =>
      addDebtPayment(debtId, {
        month: payMonth,
        year: payYear,
        amount: payAmount.trim(),
      }),
    onSuccess: () => {
      toast.success('Платёж добавлен')
      setPayAmount('')
      void queryClient.invalidateQueries({ queryKey: ['debt', debtId] })
      void queryClient.invalidateQueries({ queryKey: ['debts'] })
    },
    onError: () => {
      toast.error('Не удалось добавить платёж')
    },
  })

  if (!isAdmin) {
    return <Navigate to="/debts" replace />
  }

  if (isEdit && Number.isNaN(debtId)) {
    return <Navigate to="/debts" replace />
  }

  const payStatusValue =
    DEBT_PAYMENT_STATUS_OPTIONS.find((o) => o.value === form.payment_status) ??
    DEBT_PAYMENT_STATUS_OPTIONS[2]

  const pageTitle = isEdit
    ? detailQuery.data?.intern_name
      ? `Редактирование долга: ${detailQuery.data.intern_name}`
      : 'Редактирование долга'
    : 'Новые данные о долгах'

  return (
    <div className="page">
      <h1 className="page-title">{pageTitle}</h1>
      <div className="interview-form-back-row">
        <Link to="/debts" className="btn-secondary">
          ← К списку долгов
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
            Направление
            <Select<SelectOption<number>>
              classNamePrefix="react-select"
              isClearable
              isSearchable
              isLoading={directionsQuery.isLoading}
              options={directionOptions}
              value={directionValue}
              onChange={(opt) => setForm((f) => ({ ...f, direction_id: opt?.value ?? null }))}
            />
          </label>

          <label>
            Статус оплаты
            <Select
              classNamePrefix="react-select"
              options={DEBT_PAYMENT_STATUS_OPTIONS}
              value={payStatusValue}
              onChange={(opt) => setForm((f) => ({ ...f, payment_status: opt?.value }))}
            />
          </label>

          <label>
            Telegram (@username)
            <input
              className="form-input"
              value={form.telegram_username ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, telegram_username: e.target.value }))}
            />
          </label>

          <label>
            Email
            <input
              type="email"
              className="form-input"
              value={form.email ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </label>

          <label>
            Общая сумма
            <input
              className="form-input"
              type="text"
              inputMode="decimal"
              value={form.total_amount ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, total_amount: e.target.value }))}
            />
            {fieldErrors.total_amount ? (
              <span className="form-error">{fieldErrors.total_amount}</span>
            ) : null}
          </label>

          <label>
            Уже заплатил
            <input
              className="form-input"
              type="text"
              inputMode="decimal"
              value={form.paid_amount ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, paid_amount: e.target.value }))}
            />
          </label>

          <label>
            Дата акта
            <input
              className="form-input"
              type="date"
              value={form.act_date ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, act_date: e.target.value || null }))}
            />
          </label>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Сохранение…' : 'Сохранить'}
            </button>
            <Link to="/debts" className="btn-secondary">
              Отмена
            </Link>
          </div>
        </form>
      )}

      {isEdit && detailQuery.data ? (
        <section className="debt-payment-section" aria-label="Платежи по долгу">
          <div className="debt-payment-panel">
            <button
              type="button"
              className="debt-payment-toggle"
              aria-expanded={historyOpen}
              aria-controls="debt-payment-history-panel"
              id="debt-payment-history-heading"
              onClick={() => setHistoryOpen((v) => !v)}
            >
              <span>История платежей</span>
              <span className="debt-payment-toggle__chevron" aria-hidden>
                {historyOpen ? '▼' : '▶'}
              </span>
            </button>
            <div
              id="debt-payment-history-panel"
              role="region"
              aria-labelledby="debt-payment-history-heading"
              className={
                historyOpen ? 'debt-expandable-block debt-expandable-block--visible' : 'debt-expandable-block'
              }
            >
              <div className="interviews-subsection-card debt-payment-card-inner">
                <TableScroll className="table-scroll--plain">
                  <table className={`data-table ${DATA_TABLE_STICKY_LEADING}`}>
                    <thead>
                      <tr>
                        <th>Месяц</th>
                        <th>Год</th>
                        <th>Сумма</th>
                        <th>Создано</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailQuery.data.payment_history.map((p) => (
                        <tr key={p.id}>
                          <td>{p.month}</td>
                          <td>{p.year}</td>
                          <td>{p.amount}</td>
                          <td>{p.created_at}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </TableScroll>
              </div>
            </div>
          </div>

          <div className="debt-payment-panel">
            <button
              type="button"
              className="debt-payment-toggle"
              aria-expanded={addPaymentOpen}
              aria-controls="debt-add-payment-panel"
              id="debt-add-payment-heading"
              onClick={() => setAddPaymentOpen((v) => !v)}
            >
              <span>Добавить платёж</span>
              <span className="debt-payment-toggle__chevron" aria-hidden>
                {addPaymentOpen ? '▼' : '▶'}
              </span>
            </button>
            <div
              id="debt-add-payment-panel"
              role="region"
              aria-labelledby="debt-add-payment-heading"
              className={
                addPaymentOpen
                  ? 'debt-expandable-block debt-expandable-block--visible'
                  : 'debt-expandable-block'
              }
            >
              <div className="interviews-subsection-card debt-payment-card-inner">
                <ListPageFilterForm as="div" className="debt-add-payment-row">
                  <label>
                    Месяц
                    <input
                      className="form-input"
                      type="number"
                      min={1}
                      max={12}
                      value={payMonth}
                      onChange={(e) => setPayMonth(parseInt(e.target.value, 10) || 1)}
                    />
                  </label>
                  <label>
                    Год
                    <input
                      className="form-input"
                      type="number"
                      min={2000}
                      max={2100}
                      value={payYear}
                      onChange={(e) => setPayYear(parseInt(e.target.value, 10) || payYear)}
                    />
                  </label>
                  <label>
                    Сумма
                    <input
                      className="form-input"
                      type="text"
                      inputMode="decimal"
                      value={payAmount}
                      onChange={(e) => setPayAmount(e.target.value)}
                    />
                  </label>
                </ListPageFilterForm>
                <div className="form-actions debt-add-payment-form-actions">
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={paymentMutation.isPending || !payAmount.trim()}
                    onClick={() => paymentMutation.mutate()}
                  >
                    Добавить платёж
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  )
}
