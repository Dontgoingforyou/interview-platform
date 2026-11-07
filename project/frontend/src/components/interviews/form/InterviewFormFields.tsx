import type { Dispatch, FormEvent, SetStateAction } from 'react'
import { Link } from 'react-router-dom'
import AsyncSelect from 'react-select/async'
import AsyncCreatableSelect from 'react-select/async-creatable'
import Select from 'react-select'
import type { SingleValue } from 'react-select'

import { INTERVIEW_FORMAT_OPTIONS, INTERVIEW_TYPE_OPTIONS } from '../../../constants/interviewTypes'
import type { InterviewWritePayload } from '../../../types/interview'
import type {
  ChoiceSelectOption,
  CompanySelectOption,
  DirectionSelectOption,
  InternSelectOption,
  ManagerSelectOption,
} from './interviewFormTypes'

export interface InterviewFormFieldsProps {
  form: Partial<InterviewWritePayload>
  setForm: Dispatch<SetStateAction<Partial<InterviewWritePayload>>>
  fieldErrors: Record<string, string>
  internValue: SingleValue<InternSelectOption>
  setInternValue: (v: SingleValue<InternSelectOption>) => void
  companyValue: SingleValue<CompanySelectOption>
  setCompanyValue: (v: SingleValue<CompanySelectOption>) => void
  managerValue: SingleValue<ManagerSelectOption>
  setManagerValue: (v: SingleValue<ManagerSelectOption>) => void
  loadInternOptions: (input: string) => Promise<InternSelectOption[]>
  loadCompanyOptions: (input: string) => Promise<CompanySelectOption[]>
  directionOptions: DirectionSelectOption[]
  directionSelectValue: SingleValue<DirectionSelectOption>
  managerOptions: ManagerSelectOption[]
  interviewTypeSelectValue: SingleValue<ChoiceSelectOption>
  interviewFormatSelectValue: SingleValue<ChoiceSelectOption>
  directionsLoading: boolean
  managersLoading: boolean
  savePending: boolean
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
}

/** Поля формы создания/редактирования собеседования (без заголовка страницы и навигации). */
function InterviewFormFields({
  form,
  setForm,
  fieldErrors,
  internValue,
  setInternValue,
  companyValue,
  setCompanyValue,
  managerValue,
  setManagerValue,
  loadInternOptions,
  loadCompanyOptions,
  directionOptions,
  directionSelectValue,
  managerOptions,
  interviewTypeSelectValue,
  interviewFormatSelectValue,
  directionsLoading,
  managersLoading,
  savePending,
  onSubmit,
}: InterviewFormFieldsProps) {
  const isOnline = form.interview_format === 'online'

  return (
    <form className="interview-form" onSubmit={onSubmit}>
      <p className="interview-form-required-hint">
        Поля, отмеченные звёздочкой (*), обязательны для заполнения.
      </p>

      <label>
        Студент *
        <AsyncSelect<InternSelectOption>
          classNamePrefix="react-select"
          placeholder="Начните вводить имя…"
          loadingMessage={() => 'Загрузка…'}
          noOptionsMessage={() => 'Не найдено'}
          cacheOptions
          defaultOptions
          isClearable
          loadOptions={loadInternOptions}
          value={internValue}
          onChange={(opt) => {
            setInternValue(opt)
            if (opt) {
              setForm((f) => ({
                ...f,
                intern: opt.value,
                ...(opt.directionId != null ? { direction_id: opt.directionId } : {}),
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
        <Select<DirectionSelectOption>
          classNamePrefix="react-select"
          placeholder="Введите направление..."
          noOptionsMessage={() => 'Не найдено'}
          isClearable
          isSearchable
          isLoading={directionsLoading}
          options={directionOptions}
          value={directionSelectValue}
          onChange={(opt) => {
            setForm((f) => ({ ...f, direction_id: opt?.value }))
          }}
        />
        {fieldErrors.direction_id ? <span className="form-error">{fieldErrors.direction_id}</span> : null}
      </label>

      <label>
        Компания (поиск или новое название)
        <AsyncCreatableSelect<CompanySelectOption>
          classNamePrefix="react-select"
          cacheOptions
          defaultOptions
          isClearable
          loadOptions={loadCompanyOptions}
          value={companyValue}
          placeholder="Начните ввод или введите новую компанию…"
          loadingMessage={() => 'Загрузка…'}
          noOptionsMessage={() => 'Не найдено'}
          formatCreateLabel={(inputValue) => `Добавить компанию «${inputValue}»`}
          onChange={(opt) => {
            setCompanyValue(opt)
            const companyId: number | null =
              opt && typeof opt.value === 'number' ? opt.value : null
            setForm((f) => ({ ...f, company_id: companyId }))
          }}
        />
        {fieldErrors.company_id ? <span className="form-error">{fieldErrors.company_id}</span> : null}
        {fieldErrors.company_name ? <span className="form-error">{fieldErrors.company_name}</span> : null}
      </label>

      <label>
        Менеджер
        <Select<ManagerSelectOption>
          classNamePrefix="react-select"
          placeholder="Выберите менеджера…"
          noOptionsMessage={() => 'Не найдено'}
          isClearable
          isSearchable
          isLoading={managersLoading}
          options={managerOptions}
          value={managerValue}
          onChange={(opt) => {
            setManagerValue(opt)
            setForm((f) => ({ ...f, manager_email: opt?.value ?? '' }))
          }}
        />
        {fieldErrors.manager_email ? <span className="form-error">{fieldErrors.manager_email}</span> : null}
      </label>

      <label>
        Тип *
        <Select<ChoiceSelectOption>
          classNamePrefix="react-select"
          placeholder="Выберите тип интервью…"
          noOptionsMessage={() => 'Не найдено'}
          isClearable
          isSearchable
          options={INTERVIEW_TYPE_OPTIONS}
          value={interviewTypeSelectValue}
          onChange={(opt) => {
            setForm((f) => ({ ...f, interview_type: opt?.value }))
          }}
        />
        {fieldErrors.interview_type ? <span className="form-error">{fieldErrors.interview_type}</span> : null}
      </label>

      <label>
        Формат
        <Select<ChoiceSelectOption>
          classNamePrefix="react-select"
          placeholder="Выберите формат…"
          noOptionsMessage={() => 'Не найдено'}
          isClearable
          isSearchable
          options={INTERVIEW_FORMAT_OPTIONS}
          value={interviewFormatSelectValue}
          onChange={(opt) => {
            const fmt = opt?.value ?? 'online'
            setForm((f) => ({
              ...f,
              interview_format: fmt,
              ...(fmt !== 'online' ? { link: '' } : {}),
            }))
          }}
        />
        {fieldErrors.interview_format ? <span className="form-error">{fieldErrors.interview_format}</span> : null}
      </label>

      <label>
        Дата
        <input
          type="date"
          value={form.date ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
        />
      </label>

      <label>
        Время
        <input
          type="time"
          value={form.time ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, time: e.target.value }))}
        />
      </label>

      <div className={`interview-form-link-group${isOnline ? ' interview-form-link-group--visible' : ''}`}>
        <label>
          Ссылка на созвон
          <input
            type="url"
            value={form.link ?? ''}
            tabIndex={isOnline ? 0 : -1}
            onChange={(e) => setForm((f) => ({ ...f, link: e.target.value }))}
          />
        </label>
      </div>

      <label>
        Ссылка на вакансию
        <input
          value={form.vacancy_link ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, vacancy_link: e.target.value }))}
        />
      </label>

      <label>
        Ссылка на собеседование
        <input
          type="url"
          value={form.interview_link ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, interview_link: e.target.value }))}
        />
      </label>

      <label>
        Имя HR
        <input
          value={form.hr_name ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, hr_name: e.target.value }))}
        />
      </label>

      <label>
        Контакты HR
        <input
          value={form.hr_contacts ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, hr_contacts: e.target.value }))}
        />
      </label>

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={savePending}>
          {savePending ? 'Сохранение…' : 'Сохранить'}
        </button>
        <Link className="page-link" to="/interviews">
          Отмена
        </Link>
      </div>
    </form>
  )
}

export default InterviewFormFields
