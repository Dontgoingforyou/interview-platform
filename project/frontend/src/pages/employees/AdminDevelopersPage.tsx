import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import AdminDevelopersReport from '../../components/employees/admin/AdminDevelopersReport'
import { InlineError } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import PageIntroCard from '../../components/ui/PageIntroCard'
import { getEmployeesAdminDevelopers } from '../../api/employeesApi'
import { patchManagerUpdate } from '../../api/managersApi'
import { useToggleIndexSet } from '../../hooks/employees/useToggleIndexSet'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'

const DEV_QUERY_KEY = ['employees', 'adminDevelopers'] as const

function AdminDevelopersPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const qc = useQueryClient()

  const [showHidden, setShowHidden] = useState(false)
  const { openRows, toggleRow: toggleListRow } = useToggleIndexSet()

  const devQuery = useQuery({
    queryKey: [...DEV_QUERY_KEY, showHidden],
    queryFn: () => getEmployeesAdminDevelopers(showHidden),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ email, is_active }: { email: string; is_active: boolean }) =>
      patchManagerUpdate(email, { is_active }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: DEV_QUERY_KEY })
      toast.success('Сохранено')
    },
    onError: () => toast.error('Не удалось обновить менеджера'),
  })

  if (!isAdmin) {
    return <Navigate to="/interviews" replace />
  }

  if (devQuery.isLoading) {
    return <LoadingLine message="Загрузка отчёта…" />
  }

  if (devQuery.isError) {
    return <InlineError message="Не удалось загрузить отчёт." />
  }

  const data = devQuery.data!

  return (
    <div className="page-admin-developers">
      <PageIntroCard title="Кол-во разработчиков у менеджеров">
        <p>
          Количество активных разработчиков, закреплённых за каждым менеджером. Учитываются только студенты со
          статусом «Активный».
        </p>
      </PageIntroCard>

      <AdminDevelopersReport
        data={data}
        showHidden={showHidden}
        onShowHiddenChange={setShowHidden}
        openRows={openRows}
        onToggleListRow={toggleListRow}
        isTogglePending={toggleMutation.isPending}
        onSetManagerActive={(email, isActive) =>
          toggleMutation.mutate({ email, is_active: isActive })
        }
      />
    </div>
  )
}

export default AdminDevelopersPage
