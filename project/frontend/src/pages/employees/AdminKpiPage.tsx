import { useId, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import AdminKpiFiltersForm from '../../components/employees/admin/AdminKpiFiltersForm'
import AdminKpiResultsSection from '../../components/employees/admin/AdminKpiResultsSection'
import PageIntroCard from '../../components/ui/PageIntroCard'
import { getEmployeesAdminKpi } from '../../api/employeesApi'
import { useToggleIndexSet } from '../../hooks/employees/useToggleIndexSet'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import '../../styles/list-pages.css'

function AdminKpiPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)

  const kpiFiltersPanelId = useId()
  const [kpiFiltersExpanded, setKpiFiltersExpanded] = useState(true)

  const [draft, setDraft] = useState({ date_from: '', date_to: '', min_kpi: '3' })
  const [applied, setApplied] = useState<{
    date_from: string
    date_to: string
    min_kpi: number
  } | null>(null)
  const { openRows, toggleRow } = useToggleIndexSet()

  const kpiQuery = useQuery({
    queryKey: ['employees', 'adminKpi', applied],
    queryFn: () =>
      getEmployeesAdminKpi({
        date_from: applied!.date_from,
        date_to: applied!.date_to,
        min_kpi: applied!.min_kpi,
      }),
    enabled: applied != null,
  })

  if (!isAdmin) {
    return <Navigate to="/interviews" replace />
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const min = parseFloat(draft.min_kpi.replace(',', '.'))
    if (!draft.date_from || !draft.date_to) {
      return
    }
    if (Number.isNaN(min)) {
      return
    }
    setApplied({
      date_from: draft.date_from,
      date_to: draft.date_to,
      min_kpi: min,
    })
  }

  function handleReset() {
    setDraft({ date_from: '', date_to: '', min_kpi: '3' })
    setApplied(null)
  }

  const apiError =
    kpiQuery.error && typeof kpiQuery.error === 'object' && 'response' in kpiQuery.error
      ? (kpiQuery.error as { response?: { data?: { error?: string } } }).response?.data?.error ?? null
      : null

  const showGenericFetchError = Boolean(applied && kpiQuery.isError && !apiError)

  return (
    <div className="page-admin-kpi">
      <PageIntroCard title="KPI менеджеров по периоду">
        <p>
          Менеджеры, у которых коэффициент (собесы / активные разработчики) за неделю достигает заданного
          порога. KPI считается по той же формуле, что на вкладке «Сотрудники».
        </p>
      </PageIntroCard>

      <AdminKpiFiltersForm
        sectionId={kpiFiltersPanelId}
        expanded={kpiFiltersExpanded}
        onExpandedChange={setKpiFiltersExpanded}
        draft={draft}
        setDraft={setDraft}
        onSubmit={handleSubmit}
        onReset={handleReset}
      />

      {apiError ? <div className="alert alert-danger admin-report-alert">{apiError}</div> : null}

      <AdminKpiResultsSection
        applied={applied != null}
        isLoading={kpiQuery.isLoading}
        isSuccess={kpiQuery.isSuccess}
        data={kpiQuery.data}
        openRows={openRows}
        onToggleRow={toggleRow}
        showGenericFetchError={showGenericFetchError}
      />
    </div>
  )
}

export default AdminKpiPage
