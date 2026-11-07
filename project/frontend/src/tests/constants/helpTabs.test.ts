import { describe, expect, it } from 'vitest'

import { HELP_ACTIVE_TAB_STORAGE_KEY, HELP_TABS } from '../../constants/helpTabs'

describe('helpTabs', () => {
  it('у каждой вкладки уникальный id и Panel', () => {
    const ids = HELP_TABS.map((t) => t.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const t of HELP_TABS) {
      expect(t.label.trim().length).toBeGreaterThan(0)
      expect(typeof t.Panel).toBe('function')
    }
  })

  it('ключ storage не пустой', () => {
    expect(HELP_ACTIVE_TAB_STORAGE_KEY).toBe('helpActiveTab')
  })
})
