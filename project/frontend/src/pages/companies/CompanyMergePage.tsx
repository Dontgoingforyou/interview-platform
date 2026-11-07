import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import AsyncSelect from 'react-select/async'
import type { MultiValue, SingleValue } from 'react-select'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { mergeCompanies, searchCompaniesForSelect } from '../../api/companiesApi'
import { PageIntroCard } from '../../components/ui'
import { useAuthStore } from '../../store/authStore'
import type { SelectOption } from '../../types/common'
import { isHrOrOutstaffUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'

type CompanyOpt = SelectOption<number>

const selectStyles = { menuPortal: (base: object) => ({ ...base, zIndex: 9999 }) }

/**
 * Объединение дублей: главная компания и список дублей на удаление.
 */
function CompanyMergePage() {
  const user = useAuthStore((s) => s.user)
  const canWrite = Boolean(user && !isHrOrOutstaffUser(user))
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [primary, setPrimary] = useState<SingleValue<CompanyOpt>>(null)
  const [duplicates, setDuplicates] = useState<MultiValue<CompanyOpt>>([])

  const mergeMutation = useMutation({
    mutationFn: () => {
      if (!primary?.value) {
        throw new Error('primary')
      }
      const dupIds = duplicates.map((d) => d.value).filter((id) => id !== primary.value)
      if (!dupIds.length) {
        throw new Error('duplicates')
      }
      return mergeCompanies(primary.value, dupIds)
    },
    onSuccess: (data) => {
      toast.success(`Компании объединены. Главная: «${data.primary_name}».`)
      void queryClient.invalidateQueries({ queryKey: ['companies'] })
      navigate('/companies', { replace: true })
    },
    onError: (err: unknown) => {
      const e = err as Error
      if (e.message === 'primary') {
        toast.error('Выберите главную компанию')
        return
      }
      if (e.message === 'duplicates') {
        toast.error('Выберите хотя бы одну компанию-дубль')
        return
      }
      const ax = err as { response?: { data?: { detail?: string } } }
      const detail = ax.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Не удалось объединить компании')
    },
  })

  const loadOptions = useCallback(async (input: string): Promise<CompanyOpt[]> => {
    const list = await searchCompaniesForSelect(input)
    return list.map((c) => ({ value: c.id, label: c.name }))
  }, [])

  if (!canWrite) {
    return <Navigate to="/companies" replace />
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mergeMutation.mutate()
  }

  return (
    <div className="page company-merge-page">
      <PageIntroCard title="Объединение компаний">
        <p>
          Все собеседования дублей будут перенесены на главную компанию; названия и псевдонимы дублей
          добавятся к главной; дубли удалятся.
        </p>
      </PageIntroCard>

      <p className="company-merge-back">
        <Link to="/companies" className="btn-secondary">
          К списку компаний
        </Link>
      </p>

      <form className="company-merge-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="merge-primary">Главная компания</label>
          <AsyncSelect<CompanyOpt, false>
            inputId="merge-primary"
            cacheOptions
            defaultOptions
            loadOptions={loadOptions}
            value={primary}
            onChange={(v) => setPrimary(v)}
            placeholder="Начните вводить название…"
            classNamePrefix="react-select"
            styles={selectStyles}
            menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
            menuPosition="fixed"
            isClearable
          />
          <p className="form-hint">Собеседования дублей будут привязаны к этой записи.</p>
        </div>

        <div className="form-group">
          <label htmlFor="merge-duplicates">Дубли для удаления</label>
          <AsyncSelect<CompanyOpt, true>
            inputId="merge-duplicates"
            isMulti
            cacheOptions
            defaultOptions
            loadOptions={loadOptions}
            value={duplicates}
            onChange={(v) => setDuplicates(v)}
            placeholder="Выберите одну или несколько компаний…"
            classNamePrefix="react-select"
            styles={selectStyles}
            menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
            menuPosition="fixed"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={mergeMutation.isPending}>
            {mergeMutation.isPending ? 'Объединение…' : 'Объединить'}
          </button>
          <Link to="/companies" className="btn-secondary">
            Отмена
          </Link>
        </div>
      </form>
    </div>
  )
}

export default CompanyMergePage
