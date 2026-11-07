import { useEffect, useId, useMemo, useRef, useState } from 'react'

import {
  HELP_ACTIVE_TAB_STORAGE_KEY,
  HELP_TABS,
  type HelpTabId,
} from '../../constants/helpTabs'
import PageIntroCard from '../../components/ui/PageIntroCard'

function readStoredTabId(): HelpTabId {
  try {
    const saved = localStorage.getItem(HELP_ACTIVE_TAB_STORAGE_KEY)
    if (saved && HELP_TABS.some((t) => t.id === saved)) {
      return saved as HelpTabId
    }
  } catch {
    /* localStorage недоступен — остаёмся на вкладке по умолчанию */
  }
  return 'interviews'
}

function HelpPage() {
  const [activeTab, setActiveTab] = useState<HelpTabId>(readStoredTabId)
  const baseId = useId().replace(/:/g, '')
  const navRef = useRef<HTMLDivElement>(null)

  const tabControlsPrefix = useMemo(() => `help-tab-${baseId}`, [baseId])

  useEffect(() => {
    try {
      localStorage.setItem(HELP_ACTIVE_TAB_STORAGE_KEY, activeTab)
    } catch {
      /* ignore */
    }
    // Прокрутить навигацию к активной вкладке (нужно на мобилках с горизонтальным скроллом)
    if (navRef.current) {
      const activeBtn = navRef.current.querySelector<HTMLElement>('[aria-selected="true"]')
      activeBtn?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
    }
  }, [activeTab])

  return (
    <div className="page-stack">
      <PageIntroCard title="📖 Справка по системе">
        <p className="help-page-intro-subtitle">
          Описание разделов, расчётов и статусов простым языком. Страница доступна только администраторам — в меню
          она видна при соответствующей роли.
        </p>
      </PageIntroCard>

      <div className="help-page">
        <div ref={navRef} className="help-tabs-nav" role="tablist" aria-label="Разделы справки">
          {HELP_TABS.map((tab) => {
            const isActive = activeTab === tab.id
            const panelId = `tab-${tab.id}`
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                id={`${tabControlsPrefix}-${tab.id}`}
                className={`help-tab-btn${isActive ? ' active' : ''}`}
                aria-selected={isActive}
                aria-controls={panelId}
                tabIndex={isActive ? 0 : -1}
                data-tab={tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            )
          })}
        </div>

        {HELP_TABS.map((tab) => {
          const isActive = activeTab === tab.id
          const Panel = tab.Panel
          const panelId = `tab-${tab.id}`
          return (
            <div
              key={tab.id}
              id={panelId}
              role="tabpanel"
              className={`help-tab-content${isActive ? ' active' : ''}`}
              aria-labelledby={`${tabControlsPrefix}-${tab.id}`}
            >
              <Panel />
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default HelpPage
