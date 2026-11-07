import { useCallback, useId, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import Pagination from '../../components/Pagination'
import InterviewFilters from '../../components/interviews/InterviewFilters'
import InterviewAllTimeMetricsSection from '../../components/interviews/analytics/InterviewAllTimeMetricsSection'
import InterviewMetricsMainGrid from '../../components/interviews/analytics/InterviewMetricsMainGrid'
import InterviewTypeStatsSection from '../../components/interviews/analytics/InterviewTypeStatsSection'
import InterviewListDesktopTable from '../../components/interviews/list/InterviewListDesktopTable'
import InterviewListEmptyState from '../../components/interviews/list/InterviewListEmptyState'
import InterviewListMobileCards from '../../components/interviews/list/InterviewListMobileCards'
import InterviewListSkeleton from '../../components/interviews/list/InterviewListSkeleton'
import InterviewListTableHead from '../../components/interviews/list/InterviewListTableHead'
import InterviewListToolbar from '../../components/interviews/list/InterviewListToolbar'
import TranscriptionCell from '../../components/interviews/TranscriptionCell'
import {
  CollapsibleSection,
  ImportModal,
  InlineError,
  LoadingLine,
  PageIntroCard,
} from '../../components/ui'
import { useInterviewList } from '../../hooks/interviews/useInterviewList'
import { useAuthStore } from '../../store/authStore'
import {
  canWriteInterviews,
  isAdminUser,
  isHrOrOutstaffUser,
} from '../../utils/authRoles'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../utils/interviews/interviewTranscription'
import { hasActiveListFilters } from '../../utils/interviews/interviewListUi'
import {
  applyTableSortToSearchParams,
  withClonedSearchParams,
} from '../../utils/listPageSearchParams'
import { parseInterviewListFromSearchParams } from '../../utils/interviews/interviewListParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { runWithViewTransition } from '../../utils/viewTransition'
import type { InterviewListItem } from '../../types/interview'

/**
 * Список собеседований: только композиция секций и URL.
 * Разметка таблицы, метрик и тулбара — в components/interviews/.
 */
function InterviewsListPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const canWrite = canWriteInterviews(user)
  const showReadonlyTranscriptionColumn = isHrOrOutstaffUser(user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseInterviewListFromSearchParams(searchParams), [searchParams])

  const [allTimeExpanded, setAllTimeExpanded] = useState(false)
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [typeStatsExpanded, setTypeStatsExpanded] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const allTimePanelId = useId()
  const filtersPanelId = useId()
  const typeStatsPanelId = useId()

  const {
    analyticsQuery,
    typeBreakdownQuery,
    directionsQuery,
    managersQuery,
    deepgramQuery,
    listQuery,
    deleteMutation,
    importMutation,
    importTaskId,
    setImportTaskId,
    totalPages,
    currentPage,
    results,
  } = useInterviewList(filters, isAdmin)

  const importModalTitleId = useId()

  const onImportModalExit = useCallback(() => {
    setImportOpen(false)
    setImportTaskId(null)
  }, [setImportTaskId])

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

  const analytics = analyticsQuery.data
  const isInitialLoad =
    (analyticsQuery.isLoading && !analyticsQuery.data) ||
    (listQuery.isLoading && !listQuery.data)
  const colCount = 14 + (canWrite ? 1 : 0) + (showReadonlyTranscriptionColumn ? 1 : 0)

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
          allowStartTranscription={isAdmin}
        />
      )
    },
    [user, isAdmin],
  )

  const listIsEmpty = Boolean(listQuery.isSuccess && results.length === 0 && !listQuery.isError)
  const filtersActive = hasActiveListFilters(searchParams)

  const tableHead = (
    <InterviewListTableHead
      filters={filters}
      onToggleSort={toggleSort}
      canWrite={canWrite}
      showReadonlyTranscriptionColumn={showReadonlyTranscriptionColumn}
    />
  )

  return (
    <div className="interviews-list-page">
      <PageIntroCard title="Общая аналитика собеседований">
        <p>
          Собраны ключевые показатели по таблице «Общая таблица собеседований» за последние 30 дней:
          распределения по направлениям, менеджерам, статусам и временным периодам. Фильтры позволяют
          быстро сфокусироваться на актуальных интервью.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <InterviewListSkeleton colCount={colCount} tableHead={tableHead} />
      ) : (
        <div key="page-ready" className="interviews-page-ready">
          {analyticsQuery.isError ? <InlineError message="Не удалось загрузить аналитику." /> : null}
          {analytics ? <InterviewMetricsMainGrid analytics={analytics} /> : null}

          {analytics ? (
            <InterviewAllTimeMetricsSection
              sectionId={allTimePanelId}
              expanded={allTimeExpanded}
              onExpandedChange={setAllTimeExpanded}
              analytics={analytics}
            />
          ) : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="interviews-filters-heading"
          >
            <InterviewFilters
              searchParams={searchParams}
              managersData={managersQuery.data ?? []}
              managersLoading={managersQuery.isLoading}
              directionsData={directionsQuery.data ?? []}
              directionsLoading={directionsQuery.isLoading}
              onUpdateParams={updateFilterParams}
              onReset={resetFilters}
            />
          </CollapsibleSection>

          {typeBreakdownQuery.isError ? (
            <InlineError message="Не удалось загрузить сводку по типам." />
          ) : null}
          {typeBreakdownQuery.data && typeBreakdownQuery.data.total > 0 ? (
            <InterviewTypeStatsSection
              sectionId={typeStatsPanelId}
              expanded={typeStatsExpanded}
              onExpandedChange={setTypeStatsExpanded}
              data={typeBreakdownQuery.data}
            />
          ) : null}

          {listQuery.isError ? <InlineError message="Не удалось загрузить собеседования." /> : null}
          {listQuery.isFetching && listQuery.data ? (
            <LoadingLine message="Обновление списка…" />
          ) : null}

          <InterviewListToolbar
            isAdmin={isAdmin}
            canWrite={canWrite}
            deepgramData={deepgramQuery.data}
            deepgramLoading={deepgramQuery.isLoading}
            onImportClick={() => setImportOpen(true)}
          />

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
                <InterviewListDesktopTable
                  filters={filters}
                  onToggleSort={toggleSort}
                  results={results}
                  user={user}
                  canWrite={canWrite}
                  isAdmin={isAdmin}
                  showReadonlyTranscriptionColumn={showReadonlyTranscriptionColumn}
                  renderTranscriptionCell={renderTranscriptionCell}
                  onRequestDelete={(id) => deleteMutation.mutate(id)}
                />
                <InterviewListMobileCards
                  results={results}
                  canWrite={canWrite}
                  isAdmin={isAdmin}
                  onDelete={(id) => deleteMutation.mutate(id)}
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
        </div>
      )}

      <ImportModal
        open={importOpen}
        title="Импорт собеседований"
        description="CSV или XLSX. Обязательные колонки заданы на сервере."
        file={importFile}
        onFileChange={setImportFile}
        onExitComplete={onImportModalExit}
        onSubmit={() => importFile && importMutation.mutate(importFile)}
        pending={importMutation.isPending}
        taskId={importTaskId}
        titleId={importModalTitleId}
      />
    </div>
  )
}

export default InterviewsListPage
