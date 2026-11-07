import { SortTh } from '../../ui'
import type { DeveloperListFilters } from '../../../types/developer'

interface DeveloperListTableHeadProps {
  filters: DeveloperListFilters
  onToggleSort: (field: string) => void
}

function DeveloperListTableHead({ filters, onToggleSort }: DeveloperListTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="full_name" label="ФИО" filters={filters} onToggle={onToggleSort} className="col-dev-name" />
        <SortTh
          field="direction_name"
          label="Направление"
          filters={filters}
          onToggle={onToggleSort}
          className="col-dev-direction"
        />
        <SortTh
          field="last_activity"
          label="Последняя активность"
          filters={filters}
          onToggle={onToggleSort}
          className="col-dev-activity"
        />
        <SortTh
          field="interview_count"
          label="Интервью"
          filters={filters}
          onToggle={onToggleSort}
          className="col-dev-count"
        />
      </tr>
    </thead>
  )
}

export default DeveloperListTableHead
