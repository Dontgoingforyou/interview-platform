import { useQuery } from '@tanstack/react-query'
import { useCallback, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { postSadInternImport } from '../../api/sadInternApi'
import { getDirections } from '../../api/referenceApi'
import Pagination from '../../components/Pagination'
import SadInternMetricsMainGrid from '../../components/sadIntern/analytics/SadInternMetricsMainGrid'
import SadInternFilters from '../../components/sadIntern/filters/SadInternFilters'
import SadInternGroupSection from '../../components/sadIntern/list/SadInternGroupSection'
import SadInternListTableHead from '../../components/sadIntern/list/SadInternListTableHead'
import SadInternOnProjectTable from '../../components/sadIntern/list/SadInternOnProjectTable'
import {
  CollapsibleSection,
  GroupedListPageSkeleton,
  ImportModal,
  InlineError,
  LoadingLine,
  PageHeaderActions,
  PageIntroCard,
} from '../../components/ui'
import { DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { SAD_INTERN_METRICS_MAIN } from '../../constants/sadInternMetrics'
import { useSadInternListPage } from '../../hooks/sadIntern/useSadInternListPage'
import { useAsyncFileImport } from '../../hooks/useAsyncFileImport'
import { useAuthStore } from '../../store/authStore'
import type { SelectOption } from '../../types/common'
import { isAdminUser, isHrOrOutstaffUser } from '../../utils/authRoles'
import { withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { withClonedSearchParams } from '../../utils/listPageSearchParams'
import {
  parseSadInternListFromSearchParams,
  SAD_INTERN_LIST_META_KEYS,
} from '../../utils/sadIntern/sadInternListParams'

function applySadInternTableSort(searchParams: URLSearchParams, field: string): URLSearchParams {
  const next = new URLSearchParams(searchParams)
  const cur = next.get('order_by')
  const normalized = next.get('order_dir') === 'asc' ? 'asc' : 'desc'
  if (cur === field) {
    next.set('order_dir', normalized === 'asc' ? 'desc' : 'asc')
  } else {
    next.set('order_by', field)
    next.set('order_dir', 'desc')
  }
  for (const k of [...next.keys()]) {
    if (k.startsWith('page_')) {
      next.delete(k)
    }
  }
  next.delete('page')
  return next
}

function hasSadInternSemanticFilters(sp: URLSearchParams): boolean {
  for (const [k, v] of sp.entries()) {
    if (SAD_INTERN_LIST_META_KEYS.has(k) || k.startsWith('page_')) {
      continue
    }
    if (v) {
      return true
    }
  }
  return false
}

/**
 * Список «грустят»: метрики, фильтры, группы по направлениям, блок on_project, импорт (admin).
 */
function SadInternListPage() {
  const user = useAuthStore((s) => s.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseSadInternListFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [onProjectExpanded, setOnProjectExpanded] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const filtersPanelId = useId()
  const importModalTitleId = useId()
  const onProjectSectionId = useId()

  const isAdmin = isAdminUser(user)
  const canWrite = Boolean(user && !isHrOrOutstaffUser(user))

  const filterResetKey = useMemo(
    () =>
      JSON.stringify({
        q: filters.q ?? '',
        status: filters.status ?? '',
        direction: filters.direction ?? null,
        order_by: filters.order_by,
        order_dir: filters.order_dir,
      }),
    [filters],
  )

  const [groupPages, setGroupPages] = useState<Record<string, number>>({})
  const [prevFilterResetKey, setPrevFilterResetKey] = useState(filterResetKey)
  if (prevFilterResetKey !== filterResetKey) {
    setPrevFilterResetKey(filterResetKey)
    setGroupPages({})
  }

  const handleGroupPageChange = useCallback((key: string, page: number) => {
    setGroupPages((prev) => ({ ...prev, [key]: page }))
  }, [])

  const { analyticsQuery, groupedInfinite, mergedGroups, onProjectQuery, deleteMutation } =
    useSadInternListPage(filters, user, groupPages)

  const sadImport = useAsyncFileImport(postSadInternImport, [['sad-intern']])

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const directionOptions: SelectOption<number>[] = useMemo(
    () => (directionsQuery.data ?? []).map((d) => ({ value: d.id, label: d.name })),
    [directionsQuery.data],
  )

  const updateParams = useCallback(
    (mut: (next: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut), {
        replace: true,
        preventScrollReset: true,
      })
    },
    [searchParams, setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      setSearchParams(applySadInternTableSort(searchParams, field), {
        replace: true,
        preventScrollReset: true,
      })
    },
    [searchParams, setSearchParams],
  )

  const isInitialLoad =
    (groupedInfinite.isLoading && !groupedInfinite.data) ||
    (analyticsQuery.isLoading && !analyticsQuery.data)

  const sadInternSkeletonColCount = 8 + (canWrite ? 1 : 0)

  const onProjectCount = onProjectQuery.data?.count ?? 0
  const onProjectRows = onProjectQuery.data?.results ?? []
  const onProjectTotalPages = Math.max(1, onProjectQuery.data?.total_pages ?? 1)

  return (
    <div className="page sad-intern-list-page list-page">
      <PageIntroCard title="Разработчики, которые «грустят»">
        <p>
          Список тех, кто долго ждёт собеседований или обратной связи. Используйте фильтры, чтобы найти
          кандидатов для менторства или срочной поддержки.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <GroupedListPageSkeleton
          metricCardsCount={SAD_INTERN_METRICS_MAIN.length}
          tableHead={
            <SadInternListTableHead filters={filters} onToggleSort={toggleSort} canWrite={canWrite} />
          }
          colCount={sadInternSkeletonColCount}
          sectionClassName="sad-intern-direction-section"
          tableClassName={`data-table sad-intern-table ${DATA_TABLE_STICKY_LEADING}`}
          scrollClassName="table-scroll--plain"
        />
      ) : null}

      {!isInitialLoad ? (
        <>
          {analyticsQuery.isError ? (
            <InlineError message="Не удалось загрузить метрики." />
          ) : analyticsQuery.data ? (
            <SadInternMetricsMainGrid analytics={analyticsQuery.data} />
          ) : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="sad-intern-filters-heading"
          >
            <SadInternFilters
              filters={filters}
              directionOptions={directionOptions}
              directionsLoading={directionsQuery.isLoading}
              searchParams={searchParams}
              setSearchParams={setSearchParams}
            />
          </CollapsibleSection>

          {groupedInfinite.isFetching &&
          groupedInfinite.data &&
          !groupedInfinite.isFetchingNextPage ? (
            <LoadingLine message="Обновление списка…" />
          ) : null}
          {groupedInfinite.isError ? (
            <InlineError message="Не удалось загрузить группы по направлениям." />
          ) : null}

          {hasSadInternSemanticFilters(searchParams) && mergedGroups.length > 0 ? (
            <p className="filter-results-summary interns-filter-summary">
              Показаны направления с учётом фильтров.
            </p>
          ) : null}

          {canWrite ? (
            <div className="interviews-subsection">
              <PageHeaderActions>
                <Link className="btn-success" to="/sad-intern/new">
                  + Новый «грустный» студент
                </Link>
                {isAdmin ? (
                  <button type="button" className="btn-primary" onClick={() => setImportOpen(true)}>
                    Импортировать таблицу
                  </button>
                ) : null}
              </PageHeaderActions>
            </div>
          ) : null}

          <section
            className={withListDataRefreshingClass(
              'sad-intern-groups-section',
              Boolean(
                groupedInfinite.isFetching &&
                  groupedInfinite.data &&
                  !groupedInfinite.isFetchingNextPage,
              ),
            )}
            aria-label="Ожидают по направлениям"
          >
            {mergedGroups.length === 0 && !groupedInfinite.isFetching ? (
              <p className="alert alert-info">Нет студентов в списке ожидания.</p>
            ) : null}
            {mergedGroups.map((group) => (
              <SadInternGroupSection
                key={group.direction_id == null ? 'none' : String(group.direction_id)}
                group={group}
                filters={filters}
                groupPages={groupPages}
                onGroupPageChange={handleGroupPageChange}
                onToggleSort={toggleSort}
                canWrite={canWrite}
                isAdmin={isAdmin}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
            {groupedInfinite.hasNextPage ? (
              <div className="load-more-directions">
                <button
                  type="button"
                  className="btn-primary btn-large"
                  aria-disabled={groupedInfinite.isFetchingNextPage}
                  onClick={() => {
                    if (!groupedInfinite.isFetchingNextPage) {
                      void groupedInfinite.fetchNextPage()
                    }
                  }}
                >
                  {groupedInfinite.isFetchingNextPage ? 'Загрузка…' : 'Загрузить следующие направления'}
                </button>
              </div>
            ) : null}
          </section>

          {onProjectCount > 0 || onProjectQuery.isLoading ? (
            <CollapsibleSection
              className="sad-intern-on-project-section"
              sectionId={onProjectSectionId}
              expanded={onProjectExpanded}
              onExpandedChange={setOnProjectExpanded}
              title={`Вышли на проект (${onProjectCount})`}
              headingId="sad-intern-on-project-heading"
            >
              {onProjectQuery.isError ? (
                <InlineError message="Не удалось загрузить блок «на проекте»." />
              ) : null}
              {onProjectRows.length > 0 ? (
                <div
                  className={withListDataRefreshingClass(
                    'sad-intern-on-project-table-wrap',
                    Boolean(onProjectQuery.isFetching && onProjectQuery.data),
                  )}
                >
                  <SadInternOnProjectTable
                    rows={onProjectRows}
                    canWrite={canWrite}
                    isAdmin={isAdmin}
                    onDelete={(id) => deleteMutation.mutate(id)}
                  />
                  <Pagination
                    currentPage={filters.on_project_page}
                    totalPages={onProjectTotalPages}
                    showPageInput
                    onPageChange={(p) => {
                      updateParams((next) => {
                        next.set('on_project_page', String(p))
                      })
                    }}
                  />
                </div>
              ) : null}
            </CollapsibleSection>
          ) : null}
        </>
      ) : null}

      {isAdmin ? (
        <ImportModal
          open={importOpen}
          title="Импорт грустящих студентов"
          description={
            <p>
              CSV или XLSX. Обязательные колонки: full_name, waiting_since, telegram_username, manager_name,
              status, note (как в веб-импорте).
            </p>
          }
          file={importFile}
          onFileChange={setImportFile}
          onExitComplete={() => {
            setImportOpen(false)
            setImportFile(null)
            sadImport.setImportTaskId(null)
          }}
          onSubmit={() => {
            if (importFile) {
              sadImport.importMutation.mutate(importFile)
            }
          }}
          pending={sadImport.importMutation.isPending}
          taskId={sadImport.importTaskId}
          titleId={importModalTitleId}
        />
      ) : null}
    </div>
  )
}

export default SadInternListPage
