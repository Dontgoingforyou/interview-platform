import type { ComponentType } from 'react'

import { HelpCompaniesSection } from '../components/help/sections/HelpCompaniesSection'
import { HelpDebtsSection } from '../components/help/sections/HelpDebtsSection'
import { HelpDevelopersManagersSection } from '../components/help/sections/HelpDevelopersManagersSection'
import { HelpDevelopersSection } from '../components/help/sections/HelpDevelopersSection'
import { HelpDirectionsSection } from '../components/help/sections/HelpDirectionsSection'
import { HelpEmployeesSection } from '../components/help/sections/HelpEmployeesSection'
import { HelpImportSection } from '../components/help/sections/HelpImportSection'
import { HelpInterviewsDatabaseSection } from '../components/help/sections/HelpInterviewsDatabaseSection'
import { HelpInterviewsSection } from '../components/help/sections/HelpInterviewsSection'
import { HelpInternsSection } from '../components/help/sections/HelpInternsSection'
import { HelpKnowledgeBaseSection } from '../components/help/sections/HelpKnowledgeBaseSection'
import { HelpKpiSection } from '../components/help/sections/HelpKpiSection'
import { HelpManagersSection } from '../components/help/sections/HelpManagersSection'
import { HelpOffersSection } from '../components/help/sections/HelpOffersSection'
import { HelpSadInternSection } from '../components/help/sections/HelpSadInternSection'

export type HelpTabId =
  | 'interviews'
  | 'db'
  | 'interns'
  | 'sad'
  | 'offers'
  | 'debts'
  | 'directions'
  | 'kpi'
  | 'devmgr'
  | 'managers'
  | 'employees'
  | 'developers'
  | 'kb'
  | 'companies'
  | 'import'

export interface HelpTabConfig {
  id: HelpTabId
  label: string
  /** Панель вкладки (статический контент справки) */
  Panel: ComponentType
}

export const HELP_TABS: readonly HelpTabConfig[] = [
  { id: 'interviews', label: 'Собеседования', Panel: HelpInterviewsSection },
  { id: 'db', label: 'База собеседований', Panel: HelpInterviewsDatabaseSection },
  { id: 'interns', label: 'Студенты', Panel: HelpInternsSection },
  { id: 'sad', label: 'Грустят', Panel: HelpSadInternSection },
  { id: 'offers', label: 'Кого устроили', Panel: HelpOffersSection },
  { id: 'debts', label: 'Долги', Panel: HelpDebtsSection },
  { id: 'directions', label: 'Собесы (метрики)', Panel: HelpDirectionsSection },
  { id: 'kpi', label: 'KPI менеджеров', Panel: HelpKpiSection },
  { id: 'devmgr', label: 'Разраб. у менеджеров', Panel: HelpDevelopersManagersSection },
  { id: 'managers', label: 'Менеджеры', Panel: HelpManagersSection },
  { id: 'employees', label: 'Сотрудники', Panel: HelpEmployeesSection },
  { id: 'developers', label: 'Разработчики (период)', Panel: HelpDevelopersSection },
  { id: 'kb', label: 'База знаний', Panel: HelpKnowledgeBaseSection },
  { id: 'companies', label: 'Компании', Panel: HelpCompaniesSection },
  { id: 'import', label: 'Импорт данных', Panel: HelpImportSection },
]

export const HELP_ACTIVE_TAB_STORAGE_KEY = 'helpActiveTab'
