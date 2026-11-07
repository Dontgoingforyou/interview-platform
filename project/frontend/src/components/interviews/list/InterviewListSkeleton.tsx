import type { ReactNode } from 'react'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import ListPageSkeleton from '../../ui/ListPageSkeleton'

interface InterviewListSkeletonProps {
  colCount: number
  tableHead: ReactNode
}

/** Единый скелетон: метрики + таблица. */
function InterviewListSkeleton({ colCount, tableHead }: InterviewListSkeletonProps) {
  return (
    <ListPageSkeleton
      colCount={colCount}
      tableHead={tableHead}
      dataTableClassName={`data-table interviews-data-table ${DATA_TABLE_STICKY_LEADING}`}
      scrollClassName="table-scroll--plain"
    />
  )
}

export default InterviewListSkeleton
