import { describe, expect, it } from 'vitest'

import { KB_SECTION_DEFAULT_ICON, KB_SECTION_ICON_CHOICES } from '../../constants/kbSectionIcons'

describe('kbSectionIcons', () => {
  it('дефолтная иконка входит в набор', () => {
    expect(KB_SECTION_ICON_CHOICES).toContain(KB_SECTION_DEFAULT_ICON)
  })

  it('набор не пустой и без дублей', () => {
    expect(KB_SECTION_ICON_CHOICES.length).toBeGreaterThan(0)
    expect(new Set(KB_SECTION_ICON_CHOICES).size).toBe(KB_SECTION_ICON_CHOICES.length)
  })
})
