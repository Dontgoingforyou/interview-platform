import { SortTh } from '../../ui'
import type { DebtListFilters } from '../../../types/debt'

interface DebtListTableHeadProps {
  filters: DebtListFilters
  onToggleSort: (field: string) => void
  lastFourMonthLabels: string[]
  isAdmin: boolean
}

function DebtListTableHead({
  filters,
  onToggleSort,
  lastFourMonthLabels,
  isAdmin,
}: DebtListTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="full_name" label="ФИО студента" filters={filters} onToggle={onToggleSort} />
        <SortTh field="direction_id" label="Направление" filters={filters} onToggle={onToggleSort} />
        <th scope="col">Телеграм</th>
        <th scope="col">Email</th>
        <SortTh field="total_amount" label="Общая сумма" filters={filters} onToggle={onToggleSort} />
        <SortTh field="paid_amount" label="Уже заплатил" filters={filters} onToggle={onToggleSort} />
        <SortTh field="balance" label="Остаток" filters={filters} onToggle={onToggleSort} />
        <SortTh field="act_date" label="Дата акта" filters={filters} onToggle={onToggleSort} />
        <th scope="col" className="debts-col--spread debts-col--lastpay">
          Последний платёж (м/г)
        </th>
        {lastFourMonthLabels.map((label) => (
          <th key={label} scope="col" className="debts-col--spread debts-col--month">
            {label}
          </th>
        ))}
        <SortTh
          field="payment_status"
          label="Статус"
          filters={filters}
          onToggle={onToggleSort}
          className="debts-col--spread debts-col--status"
        />
        {isAdmin ? (
          <th scope="col" className="interviews-col-actions">
            Действия
          </th>
        ) : null}
      </tr>
    </thead>
  )
}

export default DebtListTableHead
