import { useCallback, useState } from 'react'

/** Раскрытие строк отчёта по индексу (один индекс в Set — строка «открыта»). */
export function useToggleIndexSet() {
  const [openRows, setOpenRows] = useState<Set<number>>(() => new Set())

  const toggleRow = useCallback((index: number) => {
    setOpenRows((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }, [])

  return { openRows, toggleRow }
}
