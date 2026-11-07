import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'

import { getCompany, updateCompany } from '../../api/companiesApi'
import { PageIntroCard } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import { useAuthStore } from '../../store/authStore'
import type { CompanyWritePayload } from '../../types/company'
import { isHrOrOutstaffUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'

const emptyForm: CompanyWritePayload = {
  name: '',
  is_bigtech: false,
  aliases: '',
}

/**
 * Редактирование компании (менеджеры и администраторы, не HR/outstaff).
 */
function CompanyFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const companyId = id ? parseInt(id, 10) : NaN
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const canWrite = Boolean(user && !isHrOrOutstaffUser(user))

  const [form, setForm] = useState<CompanyWritePayload>(emptyForm)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const detailQuery = useQuery({
    queryKey: ['companies', 'detail', companyId],
    queryFn: () => getCompany(companyId),
    enabled: isEdit && !Number.isNaN(companyId),
  })

  /* eslint-disable react-hooks/set-state-in-effect -- гидратация из API */
  useEffect(() => {
    const row = detailQuery.data
    if (!row) {
      return
    }
    setForm({
      name: row.name,
      is_bigtech: row.is_bigtech,
      aliases: row.aliases ?? '',
    })
  }, [detailQuery.data])
  /* eslint-enable react-hooks/set-state-in-effect */

  const saveMutation = useMutation({
    mutationFn: async () => {
      const name = form.name.trim()
      if (!name) {
        throw new Error('name')
      }
      const payload: CompanyWritePayload = {
        name,
        is_bigtech: form.is_bigtech,
        aliases: form.aliases.trim(),
      }
      return updateCompany(companyId, payload)
    },
    onSuccess: () => {
      toast.success('Компания обновлена')
      void queryClient.invalidateQueries({ queryKey: ['companies'] })
      navigate('/companies', { replace: true })
    },
    onError: (err: unknown) => {
      const e = err as Error
      if (e.message === 'name') {
        setFieldErrors({ name: 'Укажите название' })
        return
      }
      toast.error('Не удалось сохранить компанию')
    },
  })

  if (!canWrite) {
    return <Navigate to="/companies" replace />
  }

  if (!isEdit) {
    return <Navigate to="/companies" replace />
  }

  if (Number.isNaN(companyId) || detailQuery.isError) {
    return <Navigate to="/companies" replace />
  }

  if (detailQuery.isLoading) {
    return <LoadingLine message="Загрузка компании…" />
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})
    saveMutation.mutate()
  }

  return (
    <div className="page company-form-page">
      <PageIntroCard title="Редактирование компании">
        <p>
          Название, признак бигтеха и псевдонимы для импорта (по одному на строку).
        </p>
      </PageIntroCard>

      <p className="company-form-back">
        <Link to="/companies" className="btn-secondary">
          К списку компаний
        </Link>
      </p>

      <form className="company-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="company-name">Название</label>
          <input
            id="company-name"
            type="text"
            value={form.name}
            onChange={(ev) => setForm((f) => ({ ...f, name: ev.target.value }))}
            className="form-control"
            autoComplete="organization"
          />
          {fieldErrors.name ? <span className="form-error">{fieldErrors.name}</span> : null}
        </div>

        <div className="form-group form-check">
          <label htmlFor="company-bigtech">
            <input
              id="company-bigtech"
              type="checkbox"
              checked={form.is_bigtech}
              onChange={(ev) => setForm((f) => ({ ...f, is_bigtech: ev.target.checked }))}
            />{' '}
            Бигтех
          </label>
        </div>

        <div className="form-group company-form__aliases">
          <label htmlFor="company-aliases">Псевдонимы</label>
          <textarea
            id="company-aliases"
            className="form-control"
            rows={6}
            value={form.aliases}
            onChange={(ev) => setForm((f) => ({ ...f, aliases: ev.target.value }))}
            placeholder={'Один псевдоним на строку, например:\nYandex\nЯндекс.Маркет'}
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? 'Сохранение…' : 'Сохранить'}
          </button>
          <Link to="/companies" className="btn-secondary">
            Отмена
          </Link>
        </div>
      </form>
    </div>
  )
}

export default CompanyFormPage
