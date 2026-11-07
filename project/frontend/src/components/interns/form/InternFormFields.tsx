import type { Dispatch, FormEvent, SetStateAction } from 'react'
import { Link } from 'react-router-dom'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import {
  INTERN_MANUAL_STATUS_FORM_OPTIONS,
  INTERN_TRAINING_OPTIONS,
} from '../../../constants/internStatuses'
import type { SelectOption } from '../../../types/common'
import type { InternWritePayload } from '../../../types/intern'

type TrainingSelectOption = { value: string; label: string }

export interface InternFormFieldsProps {
  form: Partial<InternWritePayload>
  setForm: Dispatch<SetStateAction<Partial<InternWritePayload>>>
  fieldErrors: Record<string, string>
  directionOptions: SelectOption<number>[]
  managerOptions: SelectOption[]
  directionValue: SingleValue<SelectOption<number>>
  managerValue: SingleValue<SelectOption>
  trainingValue: TrainingSelectOption
  manualStatusValue: TrainingSelectOption
  managerSelectLocked?: boolean
  directionsLoading: boolean
  managersLoading: boolean
  savePending: boolean
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
}

/** Поля формы создания/редактирования студента (без заголовка страницы и навигации). */
function InternFormFields({
  form,
  setForm,
  fieldErrors,
  directionOptions,
  managerOptions,
  directionValue,
  managerValue,
  trainingValue,
  manualStatusValue,
  managerSelectLocked = false,
  directionsLoading,
  managersLoading,
  savePending,
  onSubmit,
}: InternFormFieldsProps) {
  return (
    <form className="interview-form" onSubmit={onSubmit}>
      <p className="interview-form-required-hint">Поля со звёздочкой (*) обязательны.</p>

      <label>
        ФИО *
        <input
          className="form-input"
          value={form.full_name ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
        />
        {fieldErrors.full_name ? <span className="form-error">{fieldErrors.full_name}</span> : null}
      </label>

      <label>
        Email
        <input
          type="email"
          className="form-input"
          value={form.email ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
        />
        {fieldErrors.email ? <span className="form-error">{fieldErrors.email}</span> : null}
      </label>

      <label>
        Telegram (@username)
        <input
          className="form-input"
          placeholder="@username"
          value={form.telegram_username ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, telegram_username: e.target.value }))}
        />
        {fieldErrors.telegram_username ? (
          <span className="form-error">{fieldErrors.telegram_username}</span>
        ) : null}
      </label>

      <label>
        Направление *
        <Select<SelectOption<number>>
          classNamePrefix="react-select"
          placeholder="Выберите направление…"
          isLoading={directionsLoading}
          options={directionOptions}
          value={directionValue}
          onChange={(opt) => setForm((f) => ({ ...f, direction_id: opt?.value }))}
        />
        {fieldErrors.direction_id ? <span className="form-error">{fieldErrors.direction_id}</span> : null}
      </label>

      <label>
        Менеджер (email)
        <Select<SelectOption>
          classNamePrefix="react-select"
          placeholder="Выберите менеджера…"
          isClearable={!managerSelectLocked}
          isDisabled={managerSelectLocked}
          isLoading={managersLoading}
          options={managerOptions}
          value={managerValue}
          onChange={(opt) => {
            if (managerSelectLocked) {
              return
            }
            setForm((f) => ({ ...f, manager_email: opt?.value ?? '' }))
          }}
        />
        {fieldErrors.manager_email ? <span className="form-error">{fieldErrors.manager_email}</span> : null}
      </label>

      <label>
        Группа *
        <input
          className="form-input"
          value={form.group ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, group: e.target.value }))}
        />
        {fieldErrors.group ? <span className="form-error">{fieldErrors.group}</span> : null}
      </label>

      <label>
        Город
        <input
          className="form-input"
          value={form.city ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
        />
        {fieldErrors.city ? <span className="form-error">{fieldErrors.city}</span> : null}
      </label>

      <label>
        Тип обучения *
        <Select
          classNamePrefix="react-select"
          options={INTERN_TRAINING_OPTIONS}
          value={trainingValue}
          onChange={(opt) => setForm((f) => ({ ...f, type_of_training: opt?.value ?? 'internal' }))}
        />
        {fieldErrors.type_of_training ? (
          <span className="form-error">{fieldErrors.type_of_training}</span>
        ) : null}
      </label>

      <label>
        Статус (ручной)
        <Select
          classNamePrefix="react-select"
          options={INTERN_MANUAL_STATUS_FORM_OPTIONS}
          value={manualStatusValue}
          onChange={(opt) => setForm((f) => ({ ...f, manual_status: opt?.value ?? '' }))}
        />
      </label>

      <label>
        Дата приёмки
        <input
          type="date"
          className="form-input"
          value={form.date_of_receipt ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, date_of_receipt: e.target.value }))}
        />
      </label>

      <label>
        Дата рождения
        <input
          type="date"
          className="form-input"
          value={form.date_of_birth ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, date_of_birth: e.target.value }))}
        />
      </label>

      <label>
        Дата выхода на реальные собеседования
        <input
          type="date"
          className="form-input"
          value={form.real_interview_date ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, real_interview_date: e.target.value }))}
        />
      </label>

      <label>
        Нанимающий HR *
        <input
          className="form-input"
          value={form.hiring_hr ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, hiring_hr: e.target.value }))}
        />
        {fieldErrors.hiring_hr ? <span className="form-error">{fieldErrors.hiring_hr}</span> : null}
      </label>

      <label>
        Ответственный HR *
        <input
          className="form-input"
          value={form.responsible_hr ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, responsible_hr: e.target.value }))}
        />
        {fieldErrors.responsible_hr ? (
          <span className="form-error">{fieldErrors.responsible_hr}</span>
        ) : null}
      </label>

      <label>
        Ссылка на резюме (URL)
        <input
          className="form-input"
          type="url"
          value={form.cv ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, cv: e.target.value }))}
        />
        {fieldErrors.cv ? <span className="form-error">{fieldErrors.cv}</span> : null}
      </label>

      <label>
        Легенда (URL)
        <input
          className="form-input"
          type="url"
          value={form.legend ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, legend: e.target.value }))}
        />
      </label>

      <label>
        Отзыв HR
        <textarea
          className="form-input"
          rows={3}
          value={form.hr_feedback ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, hr_feedback: e.target.value }))}
        />
      </label>

      <label>
        Отзыв ментора
        <textarea
          className="form-input"
          rows={3}
          value={form.mentor_feedback ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, mentor_feedback: e.target.value }))}
        />
      </label>

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={savePending}>
          {savePending ? 'Сохранение…' : 'Сохранить'}
        </button>
        <Link className="btn-secondary" to="/interns">
          Отмена
        </Link>
      </div>
    </form>
  )
}

export default InternFormFields
