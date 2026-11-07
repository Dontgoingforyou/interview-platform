import { useState } from 'react'

interface SortThProps {
  field: string
  /** Полный текст заголовка (и для подсказки, если задан collapsedLabel) */
  label: string
  /** Короткая подпись; рядом кнопка раскрывает полный `label` */
  collapsedLabel?: string
  filters: { order_by?: string; order_dir?: string }
  onToggle: (field: string) => void
  /** Дополнительные классы на `<th>` (например ширина колонки). */
  className?: string
}

/** Заголовок колонки таблицы с кнопкой сортировки. */
function SortTh({ field, label, filters, onToggle, collapsedLabel, className }: SortThProps) {
  const [labelExpanded, setLabelExpanded] = useState(false)
  const hasCollapsible = Boolean(collapsedLabel)
  const displayLabel = hasCollapsible && !labelExpanded ? collapsedLabel : label

  const active = filters.order_by === field
  const dir = filters.order_dir ?? 'desc'
  const ariaSort = active ? (dir === 'asc' ? 'ascending' : 'descending') : undefined
  const thTitle = hasCollapsible && !labelExpanded ? label : undefined

  const inner = (
    <>
      <button type="button" className="sort-header-btn" onClick={() => onToggle(field)}>
        <span className="sort-header-btn__label">{displayLabel}</span>
        {active ? (
          <span className="sort-header-btn__mark" aria-hidden>
            {dir === 'asc' ? '▲' : '▼'}
          </span>
        ) : null}
      </button>
      {hasCollapsible ? (
        <button
          type="button"
          className="sort-header-label-toggle"
          aria-expanded={labelExpanded}
          aria-label={
            labelExpanded
              ? 'Свернуть заголовок колонки'
              : `Показать полный заголовок: ${label}`
          }
          onClick={() => setLabelExpanded((v) => !v)}
        >
          {labelExpanded ? '−' : '+'}
        </button>
      ) : null}
    </>
  )

  const thClass = [
    'sortable',
    hasCollapsible ? 'sortable--collapsible-label' : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <th scope="col" className={thClass} aria-sort={ariaSort} title={thTitle}>
      {hasCollapsible ? <div className="sort-header-cell sort-header-cell--collapsible">{inner}</div> : inner}
    </th>
  )
}

export default SortTh
