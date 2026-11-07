import { useQuery } from '@tanstack/react-query'

import { getEmployeeManagers } from '../../api/employeesApi'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

export function useEmployeesManagers() {
  return useQuery({
    queryKey: ['employees', 'managers'],
    queryFn: getEmployeeManagers,
    ...paginatedListQueryOptions,
  })
}
