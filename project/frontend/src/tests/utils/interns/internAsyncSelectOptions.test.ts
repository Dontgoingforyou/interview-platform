import { describe, expect, it, vi } from 'vitest'

import type { InternOption } from '../../../api/referenceApi'
import {
  createInternAsyncSelectLoader,
  loadInternAsyncSelectOptionsMinQuery,
  mapInternToAsyncSelectOption,
} from '../../../utils/interns/internAsyncSelectOptions'

const sample: InternOption = {
  id: 7,
  full_name: 'Иван Иванов',
  direction_id: 2,
  direction_name: 'Java',
}

describe('mapInternToAsyncSelectOption', () => {
  it('маппит id/name/direction', () => {
    expect(mapInternToAsyncSelectOption(sample)).toEqual({
      value: 7,
      label: 'Иван Иванов',
      directionId: 2,
    })
  })
})

describe('loadInternAsyncSelectOptionsMinQuery', () => {
  it('не вызывает API при коротком запросе', async () => {
    const search = vi.fn()
    expect(await loadInternAsyncSelectOptionsMinQuery('a', search)).toEqual([])
    expect(search).not.toHaveBeenCalled()
  })

  it('ищет при достаточной длине', async () => {
    const search = vi.fn().mockResolvedValue([sample])
    const opts = await loadInternAsyncSelectOptionsMinQuery('ива', search)
    expect(search).toHaveBeenCalledWith('ива')
    expect(opts[0]?.value).toBe(7)
  })
})

describe('createInternAsyncSelectLoader', () => {
  it('пустой ввод → initial; непустой → search', async () => {
    const search = vi.fn().mockResolvedValue([sample])
    const loader = createInternAsyncSelectLoader({
      searchInterns: search,
      getInitialWhenEmptySearch: () => [{ ...sample, id: 1, full_name: 'Initial' }],
      map: mapInternToAsyncSelectOption,
    })
    const initial = await loader('  ')
    expect(initial[0]?.label).toBe('Initial')
    expect(search).not.toHaveBeenCalled()

    const found = await loader('иван')
    expect(search).toHaveBeenCalledWith('иван')
    expect(found[0]?.value).toBe(7)
  })
})
