import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import type { SingleValue } from 'react-select'

import {
  createInterview,
  getInterview,
  updateInterview,
} from '../../api/interviewsApi'
import {
  getCompaniesFirstPage,
  getDirections,
  getInternsPage,
  getManagersForFilters,
  searchCompanies,
  searchInterns,
  type CompanyOption,
} from '../../api/referenceApi'
import { INTERVIEW_FORMAT_OPTIONS, INTERVIEW_TYPE_OPTIONS } from '../../constants/interviewTypes'
import InterviewFormFields from '../../components/interviews/form/InterviewFormFields'
import {
  internToOption,
  type CompanySelectOption,
  type InternSelectOption,
  type ManagerSelectOption,
} from '../../components/interviews/form/interviewFormTypes'
import { useSessionFormDraft } from '../../hooks/useSessionFormDraft'
import { useAuthStore } from '../../store/authStore'
import { canWriteInterviews } from '../../utils/authRoles'
import type { InterviewWritePayload } from '../../types/interview'
import { createInternAsyncSelectLoader } from '../../utils/interns/internAsyncSelectOptions'
import { toast } from '../../utils/toast'
import { isYandexDiskPublicFileUrl } from '../../utils/yandexDiskUrl'

/**
 * Создание / редактирование / дубликат собеседования.
 * Поля формы — в components/interviews/form/InterviewFormFields.tsx.
 */
function InterviewFormPage() {
  const { id } = useParams()
  const location = useLocation()
  const isDuplicate = location.pathname.endsWith('/duplicate')
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit')
  const interviewId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<Partial<InterviewWritePayload>>({
    interview_format: 'online',
    interview_type: 'screening',
  })

  const [internValue, setInternValue] = useState<SingleValue<InternSelectOption>>(null)
  const [companyValue, setCompanyValue] = useState<SingleValue<CompanySelectOption>>(null)
  const [managerValue, setManagerValue] = useState<SingleValue<ManagerSelectOption>>(null)

  const { clearDraft } = useSessionFormDraft({
    storageKey: 'react-interview-form-draft-v1',
    form: form as unknown as Record<string, unknown>,
    setForm: setForm as Dispatch<SetStateAction<Record<string, unknown>>>,
    enabled: !isEdit && !isDuplicate,
  })

  const detailQuery = useQuery({
    queryKey: ['interview', interviewId],
    queryFn: () => getInterview(interviewId),
    enabled: (isEdit || isDuplicate) && !Number.isNaN(interviewId),
  })

  /** Сброс однократной гидратации при смене собеседования или режима (редактирование / дубликат). */
  const formHydrationKey = `${interviewId}-${isDuplicate ? 'duplicate' : 'edit'}`
  const detailHydratedRef = useRef(false)

  useEffect(() => {
    detailHydratedRef.current = false
  }, [formHydrationKey])

  const optionsQuery = useQuery({
    queryKey: ['interview-form-options'],
    queryFn: async () => {
      const [directions, interns] = await Promise.all([getDirections(), getInternsPage()])
      return { directions, interns }
    },
  })

  const managersQuery = useQuery({
    queryKey: ['managers-for-filters'],
    queryFn: getManagersForFilters,
    staleTime: 300_000,
  })

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация формы из API и подстановка label в Select */
  useEffect(() => {
    const row = detailQuery.data
    if (!row || !(isEdit || isDuplicate)) {
      return
    }
    if (row.id !== interviewId) {
      return
    }
    /* Не перезаписывать форму при каждом refetch detailQuery: иначе сбрасываются поля,
       которые пользователь уже изменил (например interview_link), и PATCH уходит со старыми данными. */
    if (detailHydratedRef.current) {
      return
    }
    detailHydratedRef.current = true
    let linkVal = row.link ?? ''
    let interviewLinkVal = row.interview_link ?? ''
    if (isDuplicate) {
      interviewLinkVal = ''
      if (linkVal && isYandexDiskPublicFileUrl(linkVal)) {
        linkVal = ''
      }
    }
    setForm({
      intern: row.intern,
      direction_id: row.direction_id ?? undefined,
      company_id: row.company_id ?? undefined,
      manager_email: row.manager_email ?? '',
      interview_type: row.interview_type,
      interview_format: row.interview_format,
      date: row.date ?? '',
      time: row.time ? row.time.slice(0, 5) : '',
      link: linkVal,
      vacancy_link: row.vacancy_link ?? '',
      interview_link: interviewLinkVal,
      hr_name: row.hr_name ?? '',
      hr_contacts: row.hr_contacts ?? '',
    })
    if (row.company_id && row.company_name) {
      setCompanyValue({ value: row.company_id, label: row.company_name })
    }
    if (row.manager_email) {
      setManagerValue({ value: row.manager_email, label: row.manager_email })
    }
  }, [detailQuery.data, interviewId, isDuplicate, isEdit])

  useEffect(() => {
    const managers = managersQuery.data
    if (!managers || !managerValue) {
      return
    }
    const found = managers.find((m) => m.email === managerValue.value)
    if (found && found.full_name !== managerValue.label) {
      setManagerValue({ value: found.email, label: found.full_name })
    }
  }, [managersQuery.data, managerValue])

  useEffect(() => {
    const interns = optionsQuery.data?.interns
    if (!interns || !form.intern) {
      return
    }
    const found = interns.find((i) => i.id === form.intern)
    if (found && internValue?.value !== found.id) {
      setInternValue(internToOption(found))
    }
  }, [optionsQuery.data?.interns, form.intern, internValue?.value])
  /* eslint-enable react-hooks/set-state-in-effect */

  const saveMutation = useMutation({
    mutationFn: async () => {
      const timeVal = form.time?.trim()
      const companyPayload: Pick<InterviewWritePayload, 'company_id' | 'company_name'> = (() => {
        if (!companyValue) {
          return { company_id: null }
        }
        if (typeof companyValue.value === 'number') {
          return { company_id: companyValue.value }
        }
        const name = companyValue.label.trim()
        return name ? { company_id: null, company_name: name } : { company_id: null }
      })()

      const payload: InterviewWritePayload = {
        intern: form.intern!,
        direction_id: form.direction_id!,
        ...companyPayload,
        manager_email: form.manager_email?.trim() || null,
        interview_type: form.interview_type!,
        interview_format: form.interview_format!,
        date: form.date?.trim() || null,
        time: timeVal ? `${timeVal}:00` : null,
        link: form.link?.trim() || null,
        vacancy_link: form.vacancy_link?.trim() || null,
        interview_link: form.interview_link?.trim() || null,
        hr_name: form.hr_name?.trim() || null,
        hr_contacts: form.hr_contacts?.trim() || null,
      }
      if (isEdit && !isDuplicate) {
        return updateInterview(interviewId, payload)
      }
      return createInterview(payload)
    },
    onSuccess: () => {
      clearDraft()
      toast.success(isEdit && !isDuplicate ? 'Сохранено' : 'Создано')
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
      if (isEdit && !isDuplicate && !Number.isNaN(interviewId)) {
        void queryClient.invalidateQueries({ queryKey: ['interview', interviewId] })
      }
      navigate('/interviews')
    },
    onError: (err: unknown) => {
      const ax = err as { response?: { data?: Record<string, string[] | string> } }
      const data = ax.response?.data
      if (data && typeof data === 'object') {
        const next: Record<string, string> = {}
        for (const [k, v] of Object.entries(data)) {
          if (k === 'detail') {
            toast.error(String(v))
          } else if (Array.isArray(v)) {
            next[k] = v.join(' ')
          } else if (typeof v === 'string') {
            next[k] = v
          }
        }
        setFieldErrors(next)
      }
      toast.error('Проверьте поля формы')
    },
  })

  const loadCompanyOptions = useMemo(
    () => async (inputValue: string) => {
      const list = inputValue.trim() ? await searchCompanies(inputValue) : await getCompaniesFirstPage()
      return list.map((c: CompanyOption) => ({ value: c.id, label: c.name }))
    },
    [],
  )

  const loadInternOptions = useMemo(
    () =>
      createInternAsyncSelectLoader({
        searchInterns,
        getInitialWhenEmptySearch: () => optionsQuery.data?.interns,
        map: internToOption,
      }),
    [optionsQuery.data?.interns],
  )

  const managerOptions = useMemo<ManagerSelectOption[]>(
    () => (managersQuery.data ?? []).map((m) => ({ value: m.email, label: m.full_name })),
    [managersQuery.data],
  )

  const directionOptions = useMemo(
    () => (optionsQuery.data?.directions ?? []).map((d) => ({ value: d.id, label: d.name })),
    [optionsQuery.data?.directions],
  )

  const directionSelectValue = useMemo((): SingleValue<{ value: number; label: string }> => {
    const dirId = form.direction_id
    if (dirId == null) {
      return null
    }
    const fromList = directionOptions.find((o) => o.value === dirId)
    if (fromList) {
      return fromList
    }
    const row = detailQuery.data
    if (row?.direction_id === dirId && row.direction_name) {
      return { value: dirId, label: row.direction_name }
    }
    return null
  }, [form.direction_id, directionOptions, detailQuery.data])

  const interviewTypeSelectValue = useMemo((): SingleValue<{ value: string; label: string }> => {
    const v = form.interview_type
    if (!v) {
      return null
    }
    return INTERVIEW_TYPE_OPTIONS.find((o) => o.value === v) ?? null
  }, [form.interview_type])

  const interviewFormatSelectValue = useMemo((): SingleValue<{ value: string; label: string }> => {
    const v = form.interview_format ?? 'online'
    return INTERVIEW_FORMAT_OPTIONS.find((o) => o.value === v) ?? null
  }, [form.interview_format])

  if (!canWriteInterviews(user)) {
    return <Navigate to="/interviews" replace />
  }

  if ((isEdit || isDuplicate) && (Number.isNaN(interviewId) || detailQuery.isError)) {
    return (
      <div>
        <p className="form-error">Собеседование не найдено.</p>
        <Link className="btn-secondary" to="/interviews">
          К списку
        </Link>
      </div>
    )
  }

  if ((isEdit || isDuplicate) && detailQuery.isLoading) {
    return <p>Загрузка…</p>
  }

  return (
    <div>
      <h1 className="page-title">
        {isDuplicate
          ? `Дубликат собеседования #${id}`
          : isEdit
            ? `Собеседование #${id}`
            : 'Новое собеседование'}
      </h1>
      <div className="interview-form-back-row">
        <Link className="btn-secondary" to="/interviews">
          ← К списку
        </Link>
      </div>

      <InterviewFormFields
        form={form}
        setForm={setForm}
        fieldErrors={fieldErrors}
        internValue={internValue}
        setInternValue={setInternValue}
        companyValue={companyValue}
        setCompanyValue={setCompanyValue}
        managerValue={managerValue}
        setManagerValue={setManagerValue}
        loadInternOptions={loadInternOptions}
        loadCompanyOptions={loadCompanyOptions}
        directionOptions={directionOptions}
        directionSelectValue={directionSelectValue}
        managerOptions={managerOptions}
        interviewTypeSelectValue={interviewTypeSelectValue}
        interviewFormatSelectValue={interviewFormatSelectValue}
        directionsLoading={optionsQuery.isLoading}
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

export default InterviewFormPage
