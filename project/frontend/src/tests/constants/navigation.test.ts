import { describe, expect, it } from 'vitest'

import {
  HR_OUTSTAFF_NAV_ORDER,
  NAV_ITEMS_MAIN,
  NAV_ITEM_HELP,
  sortNavItemsForHrOutstaff,
} from '../../constants/navigation'

describe('navigation', () => {
  it('NAV_ITEMS_MAIN содержит пути из HR порядка', () => {
    const paths = new Set(NAV_ITEMS_MAIN.map((i) => i.path))
    for (const p of HR_OUTSTAFF_NAV_ORDER) {
      expect(paths.has(p)).toBe(true)
    }
  })

  it('sortNavItemsForHrOutstaff ставит известные пути раньше прочих', () => {
    const unsorted = [
      NAV_ITEMS_MAIN.find((i) => i.path === '/employees')!,
      NAV_ITEMS_MAIN.find((i) => i.path === '/interviews')!,
      { path: '/custom', label: 'Custom' },
    ]
    const sorted = sortNavItemsForHrOutstaff(unsorted)
    expect(sorted[0]?.path).toBe('/interviews')
    expect(sorted[sorted.length - 1]?.path).toBe('/custom')
  })

  it('справка — adminOnly', () => {
    expect(NAV_ITEM_HELP.path).toBe('/help')
    expect(NAV_ITEM_HELP.adminOnly).toBe(true)
  })
})
