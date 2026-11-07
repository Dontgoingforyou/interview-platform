import { useCallback, useId, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import Pagination from '../../components/Pagination'
import InterviewsDatabaseFilters from '../../components/interviews-database/InterviewsDatabaseFilters'
import InterviewsDatabaseDesktopTable from '../../components/interviews-database/list/InterviewsDatabaseDesktopTable'
import InterviewsDatabaseMobileCards from '../../components/interviews-database/list/InterviewsDatabaseMobileCards'
import InterviewsDatabaseTableHead from '../../components/interviews-database/list/InterviewsDatabaseTableHead'
import TranscriptionCell from '../../components/interviews/TranscriptionCell'
import InterviewListEmptyState from '../../components/interviews/list/InterviewListEmptyState'
import { CollapsibleSection, InlineError, ListPageSkeleton, LoadingLine, PageIntroCard } from '../../components/ui'
import { getDirections } from '../../api/referenceApi'
import { DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { useInterviewsDatabaseList } from '../../hooks/interviewsDatabase/useInterviewsDatabaseList'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser, isHrOrOutstaffUser, isMentorUser } from '../../utils/authRoles'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../utils/interviews/interviewTranscription'
import { hasActiveListFilters } from '../../utils/interviews/interviewListUi'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { applyTableSortToSearchParams, withClonedSearchParams } from '../../utils/listPageSearchParams'
import { parseInterviewsDatabaseListFromSearchParams } from '../../utils/interviewsDatabase/interviewsDatabaseListParams'
import { runWithViewTransition } from '../../utils/viewTransition'
import type { InterviewListItem } from '../../types/interview'

/**
 * База собеседований: записи с созвоном / видео / загрузкой, фильтры и таблица.
 */
function InterviewsDatabaseListPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const canStartTranscription = isAdmin || isMentorUser(user)
  const showTranscriptionColumn = isHrOrOutstaffUser(user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(
    () => parseInterviewsDatabaseListFromSearchParams(searchParams),
    [searchParams],
  )
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const filtersPanelId = useId()

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const { listQuery, totalPages, currentPage, results } = useInterviewsDatabaseList(filters)

  const updateParams = useCallback(
    (mut: (p: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut))
    },
    [searchParams, setSearchParams],
  )

  const resetFilters = useCallback(() => {
    runWithViewTransition(() => setSearchParams(new URLSearchParams()))
  }, [setSearchParams])

  const updateFilterParams = useCallback(
    (mut: (p: URLSearchParams) => void) => {
      runWithViewTransition(() =>
        setSearchParams(withClonedSearchParams(searchParams, mut)),
      )
    },
    [searchParams, setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      updateParams((p) => {
        applyTableSortToSearchParams(p, field, 'desc')
      })
    },
    [updateParams],
  )

  const renderTranscriptionCell = useCallback(
    (row: InterviewListItem) => {
      if (!showTranscriptionControls(row) || !mayAccessInterviewTranscription(user, row)) {
        return null
      }
      return (
        <TranscriptionCell
          interviewId={row.id}
          initialStatus={row.transcription_status}
          initialErrorMessage={row.transcription_error_message}
          allowStartTranscription={canStartTranscription}
        />
      )
    },
    [user, canStartTranscription],
  )

  const listIsEmpty = Boolean(listQuery.isSuccess && results.length === 0 && !listQuery.isError)
  const filtersActive = hasActiveListFilters(searchParams)
  const tableLoading = listQuery.isLoading && !listQuery.data
  const databaseSkeletonColCount = 10 + (showTranscriptionColumn ? 1 : 0)

  return (
    <div>
      <PageIntroCard title="О разделе">
        <p>
          Список прошлых собеседований, у которых есть запись созвона, загруженное видео или идёт загрузка
          записи со стороны стажёра. Удобно искать по компании, направлению, типу интервью и статусу
          транскрибации.
        </p>
      </PageIntroCard>

      <CollapsibleSection
        sectionId={filtersPanelId}
        expanded={filtersExpanded}
        onExpandedChange={setFiltersExpanded}
        title="Поиск и фильтры"
        headingId="interviews-database-filters-heading"
      >
        <InterviewsDatabaseFilters
          searchParams={searchParams}
          directionsData={directionsQuery.data ?? []}
          directionsLoading={directionsQuery.isLoading}
          onUpdateParams={updateFilterParams}
          onReset={resetFilters}
        />
      </CollapsibleSection>

      {listQuery.isError ? (
        <InlineError message="Не удалось загрузить базу собеседований." />
      ) : null}

      {!tableLoading && listQuery.isFetching && listQuery.data ? (
        <LoadingLine message="Обновление списка…" />
      ) : null}

      {tableLoading ? (
        <section className="interviews-table-section">
          <div className="interviews-table-desktop">
            <ListPageSkeleton
              colCount={databaseSkeletonColCount}
              tableHead={
                <InterviewsDatabaseTableHead
                  filters={filters}
                  onToggleSort={toggleSort}
                  showTranscriptionColumn={showTranscriptionColumn}
                />
              }
              metricCardsCount={0}
              dataTableClassName={`data-table interviews-data-table ${DATA_TABLE_STICKY_LEADING}`}
              scrollClassName="table-scroll--plain"
            />
          </div>
        </section>
      ) : (
        <section
          className={withListDataRefreshingClass(
            'interviews-table-section',
            isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
          )}
        >
          {listIsEmpty ? (
            <InterviewListEmptyState filtersActive={filtersActive} onResetFilters={resetFilters} />
          ) : null}

          {!listIsEmpty ? (
            <>
              <InterviewsDatabaseDesktopTable
                filters={filters}
                onToggleSort={toggleSort}
                results={results}
                user={user}
                showTranscriptionColumn={showTranscriptionColumn}
                renderTranscriptionCell={renderTranscriptionCell}
              />
              <InterviewsDatabaseMobileCards
                results={results}
                user={user}
                showTranscriptionColumn={showTranscriptionColumn}
                renderTranscriptionCell={renderTranscriptionCell}
              />
            </>
          ) : null}

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={(p) => {
              updateParams((next) => {
                next.set('page', String(p))
              })
            }}
            showPageInput
          />
        </section>
      )}
    </div>
  )
}

export default InterviewsDatabaseListPage
