import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import EmployeeInternSearchPanel from '../../components/employees/list/EmployeeInternSearchPanel'
import EmployeeManagersIndexTable from '../../components/employees/list/EmployeeManagersIndexTable'
import { InlineError, ListPageSkeleton } from '../../components/ui'
import LoadingLine from '../../components/ui/LoadingLine'
import PageIntroCard from '../../components/ui/PageIntroCard'
import { getInterns } from '../../api/internsApi'
import { DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { useEmployeesManagers } from '../../hooks/employees/useEmployeesManagers'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'

/**
 * Список менеджеров и поиск студента: композиция; разметка — в components/employees/list/.
 */
function EmployeesListPage() {
  const managersQuery = useEmployeesManagers()
  const [searchQ, setSearchQ] = useState('')
  const debouncedQ = useDebouncedValue(searchQ.trim(), 300)

  const searchQuery = useQuery({
    queryKey: ['employees', 'internSearch', debouncedQ],
    queryFn: () => getInterns({ page: 1, order_by: 'id', order_dir: 'desc', q: debouncedQ }),
    enabled: debouncedQ.length >= 2,
  })

  const searchResults = useMemo(() => searchQuery.data?.results ?? [], [searchQuery.data])

  const employeesSkeletonHead = (
    <thead>
      <tr>
        <th className="col-num">#</th>
        <th>Менеджер</th>
      </tr>
    </thead>
  )

  return (
    <div className="page-employees-list">
      <PageIntroCard title="Менеджеры">
        <p>Кликните по имени менеджера, чтобы открыть его таблицу сотрудников.</p>
      </PageIntroCard>

      <EmployeeInternSearchPanel
        searchValue={searchQ}
        onSearchChange={setSearchQ}
        debouncedQ={debouncedQ}
        isFetching={searchQuery.isFetching}
        isError={searchQuery.isError}
        isSuccess={searchQuery.isSuccess}
        results={searchResults}
      />

      {managersQuery.isLoading ? (
        <ListPageSkeleton
          colCount={2}
          tableHead={employeesSkeletonHead}
          metricCardsCount={0}
          dataTableClassName={`data-table interviews-data-table employee-managers-index-table ${DATA_TABLE_STICKY_LEADING}`}
          scrollClassName="table-scroll--plain"
        />
      ) : null}
      {managersQuery.isFetching && managersQuery.data ? (
        <LoadingLine message="Обновление списка…" />
      ) : null}
      {managersQuery.isError ? <InlineError message="Не удалось загрузить список менеджеров." /> : null}

      {managersQuery.data ? (
        managersQuery.data.length === 0 ? (
          <p className="alert alert-info">Нет доступных менеджеров.</p>
        ) : (
          <div
            className={withListDataRefreshingClass(
              'employees-managers-index-wrap',
              isListBackgroundRefetch(managersQuery.isFetching, Boolean(managersQuery.data)),
            )}
          >
            <EmployeeManagersIndexTable managers={managersQuery.data} />
          </div>
        )
      ) : null}
    </div>
  )
}

export default EmployeesListPage
