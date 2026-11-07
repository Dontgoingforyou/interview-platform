import type { ReactNode } from 'react'

import { DEBT_METRICS_MAIN } from '../../../constants/debtMetrics'
import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import ListPageSkeleton from '../../ui/ListPageSkeleton'

interface DebtListSkeletonProps {
  tableHead: ReactNode
}

/** Скелетон загрузки списка долгов. */
function DebtListSkeleton({ tableHead }: DebtListSkeletonProps) {
  return (
    <div className="interns-page-skeleton">
      <ListPageSkeleton
        colCount={18}
        tableHead={tableHead}
        metricCardsCount={DEBT_METRICS_MAIN.length}
        showFiltersSkeleton
        dataTableClassName={`data-table data-table--debts ${DATA_TABLE_STICKY_LEADING}`}
        scrollClassName="table-scroll--plain debts-table-desktop"
      />
    </div>
  )
}

export default DebtListSkeleton
