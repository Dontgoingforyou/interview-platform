import { describe, expect, it } from 'vitest'

import {
  LIST_DATA_REFRESHING_CLASS,
  isListBackgroundRefetch,
  withListDataRefreshingClass,
} from '../../utils/listPageDataRefreshing'

describe('listPageDataRefreshing', () => {
  it('withListDataRefreshingClass', () => {
    expect(withListDataRefreshingClass('table', false)).toBe('table')
    expect(withListDataRefreshingClass('table', true)).toBe(`table ${LIST_DATA_REFRESHING_CLASS}`)
    expect(withListDataRefreshingClass('  ', true)).toBe(LIST_DATA_REFRESHING_CLASS)
  })

  it('isListBackgroundRefetch', () => {
    expect(isListBackgroundRefetch(true, true)).toBe(true)
    expect(isListBackgroundRefetch(true, false)).toBe(false)
    expect(isListBackgroundRefetch(false, true)).toBe(false)
  })
})
