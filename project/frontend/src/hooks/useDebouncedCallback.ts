import { useCallback, useEffect, useRef } from 'react'

/**
 * Откладывает вызов функции до паузы в `delayMs` (поиск, resize и т.п.).
 */
export function useDebouncedCallback<A extends unknown[]>(
  fn: (...args: A) => void,
  delayMs: number,
): (...args: A) => void {
  const fnRef = useRef(fn)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fnRef.current = fn
  }, [fn])

  useEffect(
    () => () => {
      if (timeoutRef.current != null) {
        clearTimeout(timeoutRef.current)
      }
    },
    [],
  )

  return useCallback(
    (...args: A) => {
      if (timeoutRef.current != null) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(() => {
        timeoutRef.current = null
        fnRef.current(...args)
      }, delayMs)
    },
    [delayMs],
  )
}
