/**
 * Пункты бокового меню: полный список и флаги для HR / admin.
 */
export interface NavItem {
  path: string
  label: string
  /** Только для manager_role === 'admin' */
  adminOnly?: boolean
  /** Показывать в меню HR и outstaff (как navbar.html для этих ролей) */
  hrVisible?: boolean
  /** Если путь начинается с этого префикса — не считать пункт активным */
  excludePrefix?: string
}

/**
 * Порядок пунктов меню HR/outstaff — как в templates/components/navbar.html.
 */
export const HR_OUTSTAFF_NAV_ORDER: readonly string[] = [
  '/interviews',
  '/interviews-database',
  '/directions',
  '/sad-intern',
  '/developers',
  '/interns',
  '/companies',
  '/managers',
  '/employees',
]

/** Основная навигация (для ролей с полным доступом; порядок — как в меню менеджера в Django). */
export const NAV_ITEMS_MAIN: NavItem[] = [
  { path: '/interviews', label: 'Собеседования', hrVisible: true },
  { path: '/interviews-database', label: 'База собеседований', hrVisible: true },
  { path: '/interns', label: 'Студенты', hrVisible: true },
  { path: '/knowledge-base', label: 'База знаний' },
  { path: '/debts', label: 'Долги', adminOnly: true },
  { path: '/offers', label: 'Кого устроили', adminOnly: true },
  { path: '/employees/admin/kpi', label: 'KPI менеджеров', adminOnly: true },
  { path: '/employees/admin/developers', label: 'Разработчики у менеджеров', adminOnly: true },
  { path: '/companies', label: 'Компании', hrVisible: true },
  { path: '/managers', label: 'Менеджеры', hrVisible: true },
  { path: '/directions', label: 'Собесы (метрики)', hrVisible: true },
  { path: '/sad-intern', label: 'Грустят', hrVisible: true },
  { path: '/employees', label: 'Сотрудники', hrVisible: true, excludePrefix: '/employees/admin' },
  { path: '/developers', label: 'Разработчики (период)', hrVisible: true },
]

export const NAV_ITEM_HELP: NavItem = {
  path: '/help',
  label: '📖 Справка по системе',
  adminOnly: true,
}

/** Сортировка пунктов меню HR/outstaff по порядку из Django-навбара. */
export function sortNavItemsForHrOutstaff(items: NavItem[]): NavItem[] {
  const order = new Map(HR_OUTSTAFF_NAV_ORDER.map((p, i) => [p, i]))
  return [...items].sort((a, b) => (order.get(a.path) ?? 999) - (order.get(b.path) ?? 999))
}
