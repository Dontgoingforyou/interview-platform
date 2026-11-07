import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { COMPANY_LIST_PAGE_SIZE, deleteCompany } from '../../api/companiesApi'
import CompanyFiltersBar from '../../components/companies/filters/CompanyListFilters'
import CompanyListMobileCards from '../../components/companies/list/CompanyListMobileCards'
import CompanyListTable from '../../components/companies/list/CompanyListTable'
import CompanyStatsSummary from '../../components/companies/list/CompanyStatsSummary'
import Pagination from '../../components/Pagination'
import {
  CollapsibleSection,
  InlineError,
  ListPageSkeleton,
  LoadingLine,
  PageHeaderActions,
  PageIntroCard,
} from '../../components/ui'
import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../constants/dataTableLayout'
import { useCompaniesListPage } from '../../hooks/companies/useCompaniesListPage'
import { useMeaningfulListFilters } from '../../hooks/useMeaningfulListFilters'
import { useAuthStore } from '../../store/authStore'
import type { CompanyListFilters, CompanyListItem } from '../../types/company'
import { isAdminUser, isHrOrOutstaffUser } from '../../utils/authRoles'
import {
  COMPANY_LIST_MEANINGFUL_FILTER_IGNORE,
  parseCompanyListFromSearchParams,
} from '../../utils/companies/companyListParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { withClonedSearchParams } from '../../utils/listPageSearchParams'
import { toast } from '../../utils/toast'

/**
 * Справочник компаний: метрики, фильтры, таблица, пагинация.
 */
function CompaniesListPage() {
  const user = useAuthStore((s) => s.user)
  const canWrite = Boolean(user && !isHrOrOutstaffUser(user))
  const isAdmin = isAdminUser(user)
  const [searchParams, setSearchParams] = useSearchParams()
  const hasSemanticFilters = useMeaningfulListFilters(searchParams, COMPANY_LIST_MEANINGFUL_FILTER_IGNORE)
  const filters = useMemo(() => parseCompanyListFromSearchParams(searchParams), [searchParams])
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const filtersPanelId = useId()
  const queryClient = useQueryClient()

  const { statsQuery, listQuery } = useCompaniesListPage(filters)

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCompany(id),
    onMutate: (id) => {
      setDeletingId(id)
    },
    onSettled: () => {
      setDeletingId(null)
    },
    onSuccess: () => {
      toast.success('Компания удалена')
      void queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
    onError: (err: unknown) => {
      const ax = err as { response?: { status?: number; data?: { detail?: string } } }
      if (ax.response?.status === 409) {
        toast.error(ax.response.data?.detail ?? 'Нельзя удалить компанию с собеседованиями')
      } else {
        toast.error('Не удалось удалить компанию')
      }
    },
  })

  const handleSortChange = useCallback(
    (sort: CompanyListFilters['sort']) => {
      setSearchParams(
        withClonedSearchParams(searchParams, (next) => {
          next.set('sort', sort)
          next.set('page', '1')
        }),
        { replace: true, preventScrollReset: true },
      )
    },
    [searchParams, setSearchParams],
  )

  const handlePageChange = useCallback(
    (page: number) => {
      setSearchParams(
        withClonedSearchParams(searchParams, (next) => {
          next.set('page', String(page))
        }),
        { replace: true, preventScrollReset: true },
      )
    },
    [searchParams, setSearchParams],
  )

  const handleDelete = useCallback(
    (row: CompanyListItem) => {
      const ok = window.confirm(
        `Удалить компанию «${row.name}»? Это действие нельзя отменить.`,
      )
      if (!ok) {
        return
      }
      deleteMutation.mutate(row.id)
    },
    [deleteMutation],
  )

  const paginated = listQuery.data
  const results = paginated?.results ?? []
  const totalCount = paginated?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(totalCount / COMPANY_LIST_PAGE_SIZE))

  const isInitialLoad = (listQuery.isLoading && !listQuery.data) || (statsQuery.isLoading && !statsQuery.data)

  const companiesSkeletonHead = (
    <thead className="table-light">
      <tr>
        <th scope="col">Название</th>
        <th scope="col">Бигтех</th>
        <th scope="col">Собеседований</th>
        <th scope="col">Псевдонимы</th>
        <th className="col-actions-header" scope="col">
          Действия
        </th>
      </tr>
    </thead>
  )

  return (
    <div className="page companies-list-page list-page">
      <PageIntroCard title="Компании">
        <p>
          {canWrite
            ? 'Справочник компаний: редактирование, удаление (только администратор), объединение дублей.'
            : 'Справочник компаний (только просмотр).'}
        </p>
      </PageIntroCard>

      {isInitialLoad ? (
        <ListPageSkeleton
          colCount={5}
          tableHead={companiesSkeletonHead}
          metricCardsCount={0}
          showFiltersSkeleton
          dataTableClassName={`data-table data-table--companies ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
          scrollClassName="table-scroll--plain companies-table-scroll"
        />
      ) : null}

      {!isInitialLoad ? (
        <>
          <CollapsibleSection
            sectionId={filtersPanelId}
            expanded={filtersExpanded}
            onExpandedChange={setFiltersExpanded}
            title="Поиск и фильтры"
            headingId="companies-filters-heading"
          >
            <CompanyFiltersBar
              filters={filters}
              searchParams={searchParams}
              setSearchParams={setSearchParams}
            />
          </CollapsibleSection>

          {canWrite ? (
            <PageHeaderActions>
              <Link className="btn-primary" to="/companies/merge">
                Объединить компании
              </Link>
            </PageHeaderActions>
          ) : null}

          {statsQuery.isError ? (
            <InlineError message="Не удалось загрузить сводку по компаниям." />
          ) : statsQuery.data ? (
            <CompanyStatsSummary stats={statsQuery.data} />
          ) : null}

          {hasSemanticFilters ? (
            <p className="filter-results-summary">Показаны компании с учётом фильтров.</p>
          ) : null}

          {listQuery.isFetching && listQuery.data ? <LoadingLine message="Обновление списка…" /> : null}
          {listQuery.isError ? <InlineError message="Не удалось загрузить список компаний." /> : null}

          {listQuery.data && results.length === 0 ? (
            <p className="text-muted">Нет компаний по текущим условиям.</p>
          ) : null}

          {results.length > 0 ? (
            <div
              className={withListDataRefreshingClass(
                'company-list-data-block',
                isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
              )}
            >
              <div className="company-list-table-wrap">
                <CompanyListTable
                  rows={results}
                  sort={filters.sort}
                  onSortChange={handleSortChange}
                  canWrite={canWrite}
                  isAdmin={isAdmin}
                  onDelete={handleDelete}
                  deletingId={deletingId}
                />
              </div>
              <div className="company-list-mobile-wrap">
                <CompanyListMobileCards
                  rows={results}
                  canWrite={canWrite}
                  isAdmin={isAdmin}
                  onDelete={handleDelete}
                  deletingId={deletingId}
                />
              </div>
              <Pagination
                currentPage={filters.page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}

export default CompaniesListPage
