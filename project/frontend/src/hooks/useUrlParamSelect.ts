import { useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import type { SingleValue } from 'react-select'

/**
 * Хук для синхронизации значения react-select с URL-параметром.
 *
 * Аналог Django `get_queryset` с фильтром из GET-параметров, но на клиенте:
 * при изменении URL-параметра хук автоматически обновляет состояние селекта.
 *
 * @param param   Значение URL-параметра (строка или null)
 * @param resolve Функция, возвращающая опцию для отображения по значению параметра
 * @returns [value, setValue] — аналог useState, но синхронизированный с URL
 */
export function useUrlParamSelect<T extends string | number>(
  param: string | null | undefined,
  resolve: (raw: string) => SingleValue<{ value: T; label: string }>,
): [SingleValue<{ value: T; label: string }>, Dispatch<SetStateAction<SingleValue<{ value: T; label: string }>>>] {
  const [value, setValue] = useState<SingleValue<{ value: T; label: string }>>(null)

  /* eslint-disable react-hooks/set-state-in-effect -- синхронизация react-select с query-string */
  useEffect(() => {
    if (param == null || param === '') {
      setValue(null)
      return
    }
    setValue((prev) => {
      const resolved = resolve(param)
      if (resolved == null) {
        return null
      }
      // Не обновляем если значение не изменилось — предотвращаем лишние ре-рендеры
      if (prev?.value === resolved.value) {
        return prev
      }
      return resolved
    })
  }, [param, resolve])
  /* eslint-enable react-hooks/set-state-in-effect */

  return [value, setValue]
}
