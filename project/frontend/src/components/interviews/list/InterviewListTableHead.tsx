import { SortTh } from '../../ui'
import type { InterviewListFilters } from '../../../types/interview'

interface InterviewListTableHeadProps {
  filters: InterviewListFilters
  onToggleSort: (field: string) => void
  canWrite: boolean
  showReadonlyTranscriptionColumn: boolean
}

function InterviewListTableHead({
  filters,
  onToggleSort,
  canWrite,
  showReadonlyTranscriptionColumn,
}: InterviewListTableHeadProps) {
  return (
    <thead className="table-light">
      <tr>
        <SortTh field="id" label="ID" filters={filters} onToggle={onToggleSort} />
        <SortTh field="full_name" label="ФИО" filters={filters} onToggle={onToggleSort} />
        <SortTh field="direction_name" label="Направление" filters={filters} onToggle={onToggleSort} />
        <SortTh field="company_name" label="Компания" filters={filters} onToggle={onToggleSort} />
        <SortTh field="interview_type" label="Тип" filters={filters} onToggle={onToggleSort} />
        <th scope="col">Формат</th>
        <SortTh field="date" label="Дата" filters={filters} onToggle={onToggleSort} />
        <SortTh field="time" label="Время" filters={filters} onToggle={onToggleSort} />
        <SortTh field="manager_name" label="Менеджер" filters={filters} onToggle={onToggleSort} />
        <SortTh field="hr_name" label="HR" filters={filters} onToggle={onToggleSort} />
        <th scope="col">Контакты HR</th>
        <th scope="col">Ссылка на созвон</th>
        <th scope="col">Вакансия</th>
        <th scope="col">Собеседование</th>
        {canWrite ? (
          <th scope="col" className="interviews-col-actions">
            Действия
          </th>
        ) : null}
        {showReadonlyTranscriptionColumn ? (
          <th scope="col" className="interviews-col-transcription">
            Транскрибация
          </th>
        ) : null}
      </tr>
    </thead>
  )
}

export default InterviewListTableHead
