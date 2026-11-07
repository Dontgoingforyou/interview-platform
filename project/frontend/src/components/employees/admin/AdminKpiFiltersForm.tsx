import type { Dispatch, FormEvent, SetStateAction } from 'react'

import { CollapsibleSection } from '../../ui'
import ListPageFilterForm from '../../ui/ListPageFilterForm'

export interface AdminKpiDraft {
  date_from: string
  date_to: string
  min_kpi: string
}

interface AdminKpiFiltersFormProps {
  sectionId: string
  expanded: boolean
  onExpandedChange: (expanded: boolean) => void
  draft: AdminKpiDraft
  setDraft: Dispatch<SetStateAction<AdminKpiDraft>>
  onSubmit: (e: FormEvent) => void
  onReset: () => void
}

export default function AdminKpiFiltersForm({
  sectionId,
  expanded,
  onExpandedChange,
  draft,
  setDraft,
  onSubmit,
  onReset,
}: AdminKpiFiltersFormProps) {
  return (
    <CollapsibleSection
      sectionId={sectionId}
      expanded={expanded}
      onExpandedChange={onExpandedChange}
      title="Параметры отчёта"
      headingId="admin-kpi-filters-heading"
    >
      <ListPageFilterForm aria-labelledby="admin-kpi-filters-heading" onSubmit={onSubmit}>
        <div className="filter-item filter-item-date">
          <span className="filter-item-date-label" id="kpi-period-label">
            Период
          </span>
          <div className="date-row" aria-labelledby="kpi-period-label">
            <input
              id="kpi-date-from"
              type="date"
              value={draft.date_from}
              onChange={(e) => setDraft((d) => ({ ...d, date_from: e.target.value }))}
              aria-label="Дата с"
            />
            <input
              id="kpi-date-to"
              type="date"
              value={draft.date_to}
              onChange={(e) => setDraft((d) => ({ ...d, date_to: e.target.value }))}
              aria-label="Дата по"
            />
          </div>
        </div>
        <div className="filter-item admin-kpi-filter-min">
          <label htmlFor="kpi-min">Мин. KPI</label>
          <input
            id="kpi-min"
            type="number"
            min={0}
            step={0.1}
            placeholder="3"
            value={draft.min_kpi}
            onChange={(e) => setDraft((d) => ({ ...d, min_kpi: e.target.value }))}
          />
        </div>
        <div className="filter-buttons">
          <label aria-hidden="true">&nbsp;</label>
          <div className="button-group">
            <button type="submit">Применить</button>
            <button type="button" onClick={onReset}>
              Сбросить
            </button>
          </div>
        </div>
      </ListPageFilterForm>
    </CollapsibleSection>
  )
}
