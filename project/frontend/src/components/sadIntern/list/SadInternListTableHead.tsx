import { SortTh } from '../../ui'
import type { SadInternListFilters } from '../../../types/sadIntern'

interface SadInternListTableHeadProps {
  filters: SadInternListFilters
  onToggleSort: (field: string) => void
  canWrite: boolean
}

/** Шапка таблицы списка «грустят» (общая для групп и скелетона). */
function SadInternListTableHead({ filters, onToggleSort, canWrite }: SadInternListTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="full_name" label="ФИО" filters={filters} onToggle={onToggleSort} />
        <SortTh field="date_joined" label="С нами с" filters={filters} onToggle={onToggleSort} />
        <SortTh field="days_waiting" label="Дней с нами" filters={filters} onToggle={onToggleSort} />
        <th className="sad-intern-th-plain" scope="col">
          <span className="sad-intern-th-plain__inner">Telegram</span>
        </th>
        <SortTh field="manager" label="Менеджер" filters={filters} onToggle={onToggleSort} />
        <SortTh field="status" label="Статус" filters={filters} onToggle={onToggleSort} />
        <th className="sad-intern-th-plain" scope="col">
          <span className="sad-intern-th-plain__inner">Примечание</span>
        </th>
        {canWrite ? (
          <th className="sad-intern-th-plain" scope="col">
            <span className="sad-intern-th-plain__inner">Действия</span>
          </th>
        ) : null}
      </tr>
    </thead>
  )
}

export default SadInternListTableHead
