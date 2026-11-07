import { SortTh } from '../../ui'
import type { InternListFilters } from '../../../types/intern'

interface InternListTableHeadProps {
  filters: InternListFilters
  onToggleSort: (field: string) => void
}

function InternListTableHead({ filters, onToggleSort }: InternListTableHeadProps) {
  return (
    <thead>
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="full_name" label="ФИО" filters={filters} onToggle={onToggleSort} />
        <SortTh field="direction_name" label="Направление" filters={filters} onToggle={onToggleSort} />
        <SortTh field="group" label="Группа" filters={filters} onToggle={onToggleSort} />
        <SortTh field="city" label="Город" filters={filters} onToggle={onToggleSort} />
        <SortTh
          field="type_of_training"
          label="Тип обучения"
          filters={filters}
          onToggle={onToggleSort}
        />
        <th>Дата приёма</th>
        <th>Дата рождения</th>
        <th>Нанимающий HR</th>
        <th>Ответственный HR</th>
        <SortTh
          field="real_interview_date"
          label="Дата выхода на реальные собесы"
          collapsedLabel="Дата выхода…"
          filters={filters}
          onToggle={onToggleSort}
        />
        <SortTh
          field="manager_name"
          label="Ответственный менеджер"
          filters={filters}
          onToggle={onToggleSort}
        />
        <th>Телеграм</th>
        <th>Email</th>
        <th>Резюме</th>
        <th>Легенда</th>
        <th scope="col" className="interviews-col-actions interns-col-actions">
          Действия
        </th>
      </tr>
    </thead>
  )
}

export default InternListTableHead
