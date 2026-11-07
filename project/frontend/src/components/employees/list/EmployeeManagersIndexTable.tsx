import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { EmployeeManagerListItem } from '../../../types/employee'

interface EmployeeManagersIndexTableProps {
  managers: EmployeeManagerListItem[]
}

export default function EmployeeManagersIndexTable({ managers }: EmployeeManagersIndexTableProps) {
  return (
    <TableScroll className="table-scroll--plain">
      <table
        className={`data-table interviews-data-table employee-managers-index-table ${DATA_TABLE_STICKY_LEADING}`}
      >
        <thead>
          <tr>
            <th className="col-num">#</th>
            <th>Менеджер</th>
          </tr>
        </thead>
        <tbody>
          {managers.map((m, idx) => (
            <tr key={m.email}>
              <td className="td-muted">{idx + 1}</td>
              <td>
                <Link to={`/employees/${encodeURIComponent(m.email)}`}>
                  <strong>{m.full_name}</strong>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  )
}
