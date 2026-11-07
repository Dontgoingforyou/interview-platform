import { describe, expect, it } from 'vitest'

import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

describe('paginatedListQueryOptions', () => {
  it('держит placeholderData keepPreviousData', () => {
    expect(paginatedListQueryOptions.placeholderData).toBeTypeOf('function')
  })
})
