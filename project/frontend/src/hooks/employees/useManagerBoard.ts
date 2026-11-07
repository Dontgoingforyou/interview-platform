import { useQuery } from '@tanstack/react-query'

import { getManagerBoard } from '../../api/employeesApi'

export const managerBoardQueryKey = (email: string) => ['employees', 'board', email] as const

export function useManagerBoard(managerEmail: string | undefined) {
  return useQuery({
    queryKey: managerEmail ? managerBoardQueryKey(managerEmail) : ['employees', 'board', ''],
    queryFn: () => getManagerBoard(managerEmail!),
    enabled: Boolean(managerEmail && managerEmail.length > 0),
  })
}
