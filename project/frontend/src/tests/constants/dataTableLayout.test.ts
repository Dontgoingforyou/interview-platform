import { describe, expect, it } from 'vitest'

import {
  DATA_TABLE_STICKY_FIRST_COL_ONLY,
  DATA_TABLE_STICKY_LEADING,
} from '../../constants/dataTableLayout'

describe('dataTableLayout', () => {
  it('CSS-модификаторы sticky колонок', () => {
    expect(DATA_TABLE_STICKY_LEADING).toBe('data-table--sticky-leading')
    expect(DATA_TABLE_STICKY_FIRST_COL_ONLY).toBe('data-table--sticky-first-col-only')
  })
})
