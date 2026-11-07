import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { CompanyListItem, CompanyListFilters } from '../../../types/company'

function aliasesPreview(lines: string[], maxLen: number): string {
  if (!lines.length) {
    return ''
  }
  const s = lines.join(', ')
  if (s.length <= maxLen) {
    return s
  }
  return `${s.slice(0, maxLen)}…`
}

function nextSortForColumn(
  column: 'name' | 'interviews',
  current: CompanyListFilters['sort'],
): CompanyListFilters['sort'] {
  if (column === 'name') {
    return current === 'name' ? '-name' : 'name'
  }
  return current === 'interviews' ? '-interviews' : 'interviews'
}

type Props = {
  rows: CompanyListItem[]
  sort: CompanyListFilters['sort']
  onSortChange: (sort: CompanyListFilters['sort']) => void
  canWrite: boolean
  isAdmin: boolean
  onDelete: (row: CompanyListItem) => void
  deletingId: number | null
}

/**
 * Десктопная таблица компаний с сортировкой по названию и числу собеседований.
 */
function CompanyListTable({ rows, sort, onSortChange, canWrite, isAdmin, onDelete, deletingId }: Props) {
  return (
    <TableScroll className="table-scroll--plain companies-table-scroll">
      <table
        className={`data-table data-table--companies ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
      >
        <colgroup>
          <col className="col-company-name" />
          <col className="col-company-bigtech" />
          <col className="col-company-count" />
          <col className="col-company-aliases" />
          <col className="col-company-actions" />
        </colgroup>
        <thead className="table-light">
          <tr>
            <th scope="col">
              <button
                type="button"
                className="table-sort-btn"
                onClick={() => onSortChange(nextSortForColumn('name', sort))}
              >
                Название
                {sort === 'name' ? ' ▲' : null}
                {sort === '-name' ? ' ▼' : null}
              </button>
            </th>
            <th scope="col">Бигтех</th>
            <th scope="col">
              <button
                type="button"
                className="table-sort-btn"
                onClick={() => onSortChange(nextSortForColumn('interviews', sort))}
              >
                Собеседований
                {sort === 'interviews' ? ' ▼' : null}
                {sort === '-interviews' ? ' ▲' : null}
              </button>
            </th>
            <th scope="col">Псевдонимы</th>
            <th className="col-actions-header" scope="col">
              Действия
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const preview = aliasesPreview(row.aliases_list, 105)
            return (
              <tr key={row.id}>
                <td>
                  <strong>{row.name}</strong>
                </td>
                <td>
                  {row.is_bigtech ? <span className="status-active">Да</span> : <span className="text-muted">—</span>}
                </td>
                <td>
                  {row.interviews_count > 0 ? (
                    <Link to={`/interviews?company=${row.id}`}>{row.interviews_count}</Link>
                  ) : (
                    <span className="text-muted">0</span>
                  )}
                </td>
                <td>
                  {preview ? (
                    <span title={row.aliases_list.join(', ')}>{preview}</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
                <td className="action-buttons">
                  {canWrite ? (
                    <Link
                      to={`/companies/${row.id}/edit`}
                      className="btn-outline-primary btn-small interviews-action-emoji"
                      title="Редактировать"
                    >
                      ✏️
                    </Link>
                  ) : null}
                  {isAdmin ? (
                    <button
                      type="button"
                      className="btn-outline-danger btn-small interviews-action-emoji"
                      title="Удалить"
                      disabled={deletingId === row.id}
                      onClick={() => onDelete(row)}
                    >
                      🗑️
                    </button>
                  ) : null}
                  {!canWrite && !isAdmin ? <span className="text-muted">—</span> : null}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default CompanyListTable
