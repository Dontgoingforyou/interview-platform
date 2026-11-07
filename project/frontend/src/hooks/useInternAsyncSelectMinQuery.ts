import { useCallback } from 'react'

import { searchInterns } from '../api/referenceApi'
import { loadInternAsyncSelectOptionsMinQuery } from '../utils/interns/internAsyncSelectOptions'

/**
 * loadOptions для AsyncSelect стажёра: от двух символов в строке поиска.
 */
export function useInternAsyncSelectMinQuery() {
  return useCallback((input: string) => loadInternAsyncSelectOptionsMinQuery(input, searchInterns), [])
}
