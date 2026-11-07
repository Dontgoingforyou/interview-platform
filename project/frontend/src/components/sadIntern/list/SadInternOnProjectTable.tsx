import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import TableScroll from '../../ui/TableScroll'
import SadInternOnProjectMobileCards from './SadInternOnProjectMobileCards'
import type { SadInternListItem } from '../../../types/sadIntern'
import { formatRuDate } from '../../../utils/dateFormat'
import { telegramHref } from '../../../utils/debts/debtTableDisplay'

interface SadInternOnProjectTableProps {
  rows: SadInternListItem[]
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

function PlainTh({ children }: { children: ReactNode }) {
  return (
    <th className="sad-intern-th-plain">
      <span className="sad-intern-th-plain__inner">{children}</span>
    </th>
  )
}

/** Таблица блока «Вышли на проект». */
function SadInternOnProjectTable({ rows, canWrite, isAdmin, onDelete }: SadInternOnProjectTableProps) {
  return (
    <Fragment>
      <div className="sad-intern-table-desktop">
        <TableScroll className="table-scroll--plain">
          <table className={`data-table sad-intern-table ${DATA_TABLE_STICKY_LEADING}`}>
            <thead className="table-light">
              <tr>
                <PlainTh>ID</PlainTh>
                <PlainTh>ФИО</PlainTh>
                <PlainTh>Направление</PlainTh>
                <PlainTh>С нами с</PlainTh>
                <PlainTh>Вышел на проект</PlainTh>
                <PlainTh>Telegram</PlainTh>
                <PlainTh>Менеджер</PlainTh>
                <PlainTh>Примечание</PlainTh>
                {canWrite ? <PlainTh>Действия</PlainTh> : null}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const tgUrl = telegramHref(row.telegram_username ?? '')
                return (
                  <tr key={row.id} className="status-positive">
                    <td>{row.id}</td>
                    <td>{row.intern_name}</td>
                    <td>{row.direction_name ?? '—'}</td>
                    <td>{formatRuDate(row.real_interview_date)}</td>
                    <td>{formatRuDate(row.date_added)}</td>
                    <td>
                      {tgUrl ? (
                        <a href={tgUrl} target="_blank" rel="noopener noreferrer">
                          {row.telegram_username}
                        </a>
                      ) : (
                        (row.telegram_username ?? '—')
                      )}
                    </td>
                    <td>{row.intern_manager_name ?? '—'}</td>
                    <td>{row.note?.trim() ? row.note : '—'}</td>
                    {canWrite ? (
                      <td className="action-buttons">
                        <Link
                          to={`/sad-intern/${row.id}/edit`}
                          className="btn-outline-primary btn-small"
                          title="Редактировать"
                        >
                          ✏️
                        </Link>
                        {isAdmin ? (
                          <button
                            type="button"
                            className="btn-outline-danger btn-small"
                            title="Удалить"
                            onClick={() => {
                              if (window.confirm('Удалить запись? Это действие нельзя отменить.')) {
                                onDelete(row.id)
                              }
                            }}
                          >
                            🗑️
                          </button>
                        ) : null}
                      </td>
                    ) : null}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </TableScroll>
      </div>
      <SadInternOnProjectMobileCards
        rows={rows}
        canWrite={canWrite}
        isAdmin={isAdmin}
        onDelete={onDelete}
      />
    </Fragment>
  )
}

export default SadInternOnProjectTable
