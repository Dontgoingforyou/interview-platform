import { Link } from 'react-router-dom'

import { PageHeaderActions } from '../../ui'
import { deepgramBalanceLabel } from '../../../utils/interviews/interviewMetricsDisplay'

interface InterviewListToolbarProps {
  isAdmin: boolean
  canWrite: boolean
  deepgramData: { amount?: number | null; error?: string } | undefined
  deepgramLoading: boolean
  onImportClick: () => void
}

/** Кнопки над таблицей: Deepgram, таблица, новое, импорт. */
function InterviewListToolbar({
  isAdmin,
  canWrite,
  deepgramData,
  deepgramLoading,
  onImportClick,
}: InterviewListToolbarProps) {
  const dg = deepgramBalanceLabel(deepgramData, deepgramLoading)

  return (
    <div className="interviews-subsection">
      <PageHeaderActions>
        {isAdmin ? (
          <span
            className={`badge badge-info${dg.isError ? ' badge-error' : ''}`}
            title={deepgramData?.error ?? 'Баланс Deepgram API'}
          >
            {dg.text}
          </span>
        ) : null}
        {canWrite ? (
          <Link className="btn-success" to="/interviews/new">
            + Новое собеседование
          </Link>
        ) : null}
        {isAdmin ? (
          <button type="button" className="btn-primary" onClick={onImportClick}>
            Импортировать таблицу
          </button>
        ) : null}
      </PageHeaderActions>
    </div>
  )
}

export default InterviewListToolbar
