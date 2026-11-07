import { useCallback, useId, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { deleteOffer, postOfferImport } from '../../api/offersApi'
import { getDirections } from '../../api/referenceApi'
import OfferMetricsMainGrid from '../../components/offers/analytics/OfferMetricsMainGrid'
import OfferFilters from '../../components/offers/filters/OfferFilters'
import OfferMonthSection from '../../components/offers/list/OfferMonthSection'
import OfferListTableHead from '../../components/offers/list/OfferListTableHead'
import {
  CollapsibleSection,
  GroupedListPageSkeleton,
  ImportModal,
  InlineError,
  LoadingLine,
  PageHeaderActions,
  PageIntroCard,
} from '../../components/ui'
import { useAsyncFileImport } from '../../hooks/useAsyncFileImport'
import { OFFER_METRICS_MAIN } from '../../constants/offerMetrics'
import { useOffersListPage } from '../../hooks/offers/useOffersListPage'
import { useMeaningfulListFilters } from '../../hooks/useMeaningfulListFilters'
import { useAuthStore } from '../../store/authStore'
import type { OfferMonthGroupRow } from '../../types/offer'
import { parseOfferListFromSearchParams } from '../../utils/offers/offerListParams'
import { withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { applyTableSortToSearchParams, withClonedSearchParams } from '../../utils/listPageSearchParams'

function monthSectionKey(g: OfferMonthGroupRow): string {
  return `${g.year}-${g.month}`
}

/**
 * Список офферов: аналитика, фильтры, группы по месяцам с пагинацией.
 */
function OffersListPage() {
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const hasActiveSemanticFilters = useMeaningfulListFilters(searchParams)
  const filters = useMemo(() => parseOfferListFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [pageByMonth, setPageByMonth] = useState<Record<string, number>>({})
  const filtersPanelId = useId()
  const importModalTitleId = useId()

  const filterResetKey = useMemo(
    () =>
      JSON.stringify({
        q: filters.q ?? '',
        year: filters.year ?? null,
        month: filters.month ?? null,
        direction_id: filters.direction_id ?? null,
        order_by: filters.order_by ?? '',
        order_dir: filters.order_dir ?? '',
      }),
    [filters],
  )
  const [prevFilterResetKey, setPrevFilterResetKey] = useState(filterResetKey)
  if (prevFilterResetKey !== filterResetKey) {
    setPrevFilterResetKey(filterResetKey)
    setPageByMonth({})
  }

  const offerImport = useAsyncFileImport(postOfferImport, [['offers']])

  const deleteOfferMutation = useMutation({
    mutationFn: deleteOffer,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['offers'] })
    },
  })

  const directionsQuery = useQuery({
    queryKey: ['directions-options'],
    queryFn: getDirections,
    staleTime: 300_000,
  })

  const { isAdmin, analyticsQuery, monthGroupsInfinite, groups, listQueries } = useOffersListPage(
    filters,
    pageByMonth,
    user,
  )

  const directionOptions = useMemo(
    () =>
      (directionsQuery.data ?? []).map((d) => ({
        value: d.id,
        label: d.name,
      })),
    [directionsQuery.data],
  )

  const updateParams = useCallback(
    (mut: (next: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut), { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      updateParams((next) => {
        applyTableSortToSearchParams(next, field, 'desc')
      })
    },
    [updateParams],
  )

  const isInitialLoad =
    (analyticsQuery.isLoading && !analyticsQuery.data) ||
    (monthGroupsInfinite.isLoading && !monthGroupsInfinite.data)

  return (
    <div className="page offers-list-page">
      <PageIntroCard title="Кого и куда устроили">
        <p>
          Раздел собирает записи по трудоустройствам: офферы, направления, компании и суммы по месяцам.
          Фильтры и метрики помогают отследить динамику и работодателей.
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <GroupedListPageSkeleton
          metricCardsCount={OFFER_METRICS_MAIN.length}
          tableHead={<OfferListTableHead filters={filters} onToggleSort={toggleSort} />}
          colCount={7}
        />
      ) : (
        <div key="page-ready" className="interns-page-ready">
          {analyticsQuery.isError ? (
            <InlineError message="Не удалось загрузить аналитику офферов." />
          ) : null}
          {analyticsQuery.data ? <OfferMetricsMainGrid analytics={analyticsQuery.data} /> : null}

          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="offers-filters-heading"
          >
            <OfferFilters
              filters={filters}
              directionOptions={directionOptions}
              directionsLoading={directionsQuery.isLoading}
              searchParams={searchParams}
              setSearchParams={setSearchParams}
            />
          </CollapsibleSection>

          {monthGroupsInfinite.isFetching && monthGroupsInfinite.data ? (
            <LoadingLine message="Обновление списка месяцев…" />
          ) : null}

          {monthGroupsInfinite.isError ? (
            <InlineError message="Не удалось загрузить группы по месяцам." />
          ) : null}

          {hasActiveSemanticFilters ? (
            <p className="filter-results-summary interns-filter-summary">
              Показаны периоды с учётом фильтров. Подгрузка месяцев — кнопкой ниже.
            </p>
          ) : null}

          {isAdmin ? (
            <div className="interviews-subsection">
              <PageHeaderActions>
                <Link className="btn-success" to="/offers/new">
                  + Новый оффер
                </Link>
                <button type="button" className="btn-primary" onClick={() => setImportOpen(true)}>
                  Импортировать таблицу
                </button>
              </PageHeaderActions>
            </div>
          ) : null}

          {!monthGroupsInfinite.isLoading && !monthGroupsInfinite.isError ? (
            <div
              className={withListDataRefreshingClass(
                'offers-months-container',
                Boolean(
                  monthGroupsInfinite.isFetching &&
                    monthGroupsInfinite.data &&
                    !monthGroupsInfinite.isFetchingNextPage,
                ),
              )}
              id="months-container"
            >
              {groups.length === 0 ? (
                <div className="alert alert-info">Нет офферов.</div>
              ) : (
                groups.map((g, index) => {
                  const key = monthSectionKey(g)
                  const listQuery = listQueries[index]
                  if (!listQuery) {
                    return null
                  }
                  return (
                    <OfferMonthSection
                      key={key}
                      group={g}
                      listQuery={listQuery}
                      currentPage={pageByMonth[key] ?? 1}
                      onPageChange={(p) => {
                        setPageByMonth((prev) => ({ ...prev, [key]: p }))
                      }}
                      filters={filters}
                      onToggleSort={toggleSort}
                      isAdmin={isAdmin}
                      onDeleteOffer={(id) => deleteOfferMutation.mutate(id)}
                    />
                  )
                })
              )}

              {monthGroupsInfinite.hasNextPage ? (
                <div className="load-more-months">
                  <button
                    type="button"
                    className="btn-primary btn-large"
                    disabled={monthGroupsInfinite.isFetchingNextPage}
                    onClick={() => void monthGroupsInfinite.fetchNextPage()}
                  >
                    {monthGroupsInfinite.isFetchingNextPage
                      ? 'Загрузка…'
                      : 'Загрузить следующие месяцы'}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      )}

      {isAdmin ? (
        <ImportModal
          open={importOpen}
          title="Импорт офферов"
          description={
            <p>
              CSV или XLSX. Обязательные колонки: ФИО, направление, компания, сумма (как в шаблоне импорта
              Django).
            </p>
          }
          file={importFile}
          onFileChange={setImportFile}
          onExitComplete={() => {
            setImportOpen(false)
            setImportFile(null)
            offerImport.setImportTaskId(null)
          }}
          onSubmit={() => {
            if (importFile) {
              offerImport.importMutation.mutate(importFile)
            }
          }}
          pending={offerImport.importMutation.isPending}
          taskId={offerImport.importTaskId}
          titleId={importModalTitleId}
        />
      ) : null}
    </div>
  )
}

export default OffersListPage
