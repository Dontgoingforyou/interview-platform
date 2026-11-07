/**
 * Набор иконок раздела базы знаний (как в легаси knowledge_base.html).
 */
export const KB_SECTION_ICON_CHOICES = ['📚', '📁', '🔑', '📝', '💼', '⚙️', '🎓', '💡', '🚀', '📊'] as const

export type KbSectionIconChoice = (typeof KB_SECTION_ICON_CHOICES)[number]

export const KB_SECTION_DEFAULT_ICON: KbSectionIconChoice = '📚'
