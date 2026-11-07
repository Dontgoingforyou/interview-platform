import { SortTh } from '../../ui'
import type { InterviewsDatabaseListFilters } from '../../../types/interview'

interface InterviewsDatabaseTableHeadProps {
  filters: InterviewsDatabaseListFilters
  onToggleSort: (field: string) => void
  showTranscriptionColumn: boolean
}

function InterviewsDatabaseTableHead({
  filters,
  onToggleSort,
  showTranscriptionColumn,
}: InterviewsDatabaseTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="full_name" label="ФИО" filters={filters} onToggle={onToggleSort} />
        <SortTh field="company_name" label="Компания" filters={filters} onToggle={onToggleSort} />
        <SortTh field="direction_name" label="Направление" filters={filters} onToggle={onToggleSort} />
        <SortTh field="interview_type" label="Тип" filters={filters} onToggle={onToggleSort} />
        <SortTh field="date" label="Дата" filters={filters} onToggle={onToggleSort} />
        <SortTh field="hr_name" label="HR" filters={filters} onToggle={onToggleSort} />
        <th scope="col">Контакты HR</th>
        <th scope="col">Запись созвона</th>
        <th scope="col">Вакансия</th>
        {showTranscriptionColumn ? (
          <th scope="col" className="interviews-col-transcription">
            Транскрибация
          </th>
        ) : null}
      </tr>
    </thead>
  )
}

export default InterviewsDatabaseTableHead
