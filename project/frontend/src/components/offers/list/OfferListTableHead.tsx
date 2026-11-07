import { SortTh } from '../../ui'
import type { OfferListFilters } from '../../../types/offer'

interface OfferListTableHeadProps {
  filters: OfferListFilters
  onToggleSort: (field: string) => void
}

/** Шапка таблицы офферов с сортировкой */
function OfferListTableHead({ filters, onToggleSort }: OfferListTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="intern_name" label="ФИО" filters={filters} onToggle={onToggleSort} />
        <SortTh field="direction_name" label="Направление" filters={filters} onToggle={onToggleSort} />
        <SortTh field="company" label="Компания" filters={filters} onToggle={onToggleSort} />
        <SortTh field="amount" label="Сумма" filters={filters} onToggle={onToggleSort} />
        <th scope="col">Телеграм</th>
        <th scope="col" className="interviews-col-actions">Действия</th>
      </tr>
    </thead>
  )
}

export default OfferListTableHead
