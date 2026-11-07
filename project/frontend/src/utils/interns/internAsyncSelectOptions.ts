import type { InternOption } from '../../api/referenceApi'
import type { SelectOption } from '../../types/common'

/** Опция стажёра для react-select/async (офферы, долги и т.п.). */
export type InternAsyncSelectOption = SelectOption<number> & { directionId?: number | null }

export function mapInternToAsyncSelectOption(i: InternOption): InternAsyncSelectOption {
  return {
    value: i.id,
    label: i.full_name,
    directionId: i.direction_id,
  }
}

/**
 * Поиск стажёров для AsyncSelect: при коротком запросе — пустой список (не дергать API).
 */
export async function loadInternAsyncSelectOptionsMinQuery(
  input: string,
  searchInterns: (q: string) => Promise<InternOption[]>,
  minQueryLength = 2,
): Promise<InternAsyncSelectOption[]> {
  if (!input || input.trim().length < minQueryLength) {
    return []
  }
  const list = await searchInterns(input.trim())
  return list.map(mapInternToAsyncSelectOption)
}

/**
 * Загрузчик для формы собеседований: при пустом вводе — первая страница стажёров из query.
 */
export function createInternAsyncSelectLoader<T>(options: {
  searchInterns: (q: string) => Promise<InternOption[]>
  getInitialWhenEmptySearch: () => InternOption[] | undefined
  map: (i: InternOption) => T
}): (inputValue: string) => Promise<T[]> {
  const { searchInterns, getInitialWhenEmptySearch, map } = options
  return async (inputValue: string) => {
    if (inputValue.trim()) {
      const list = await searchInterns(inputValue.trim())
      return list.map(map)
    }
    return (getInitialWhenEmptySearch() ?? []).map(map)
  }
}
