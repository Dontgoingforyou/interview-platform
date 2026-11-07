import { useCallback, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import InternFilters from '../../components/interns/InternFilters'
import InternListDesktopTable from '../../components/interns/list/InternListDesktopTable'
import InternListEmptyState from '../../components/interns/list/InternListEmptyState'
import InternListMobileCards from '../../components/interns/list/InternListMobileCards'
import InternListSkeleton from '../../components/interns/list/InternListSkeleton'
import InternListTableHead from '../../components/interns/list/InternListTableHead'
import Pagination from '../../components/Pagination'
import { CollapsibleSection, ImportModal, InlineError, LoadingLine, PageHeaderActions, PageIntroCard } from '../../components/ui'
import { useInternsList } from '../../hooks/interns/useInternsList'
import { useMeaningfulListFilters } from '../../hooks/useMeaningfulListFilters'
import { useAuthStore } from '../../store/authStore'
import { canWriteInterviews, isAdminUser } from '../../utils/authRoles'
import { parseInternListFromSearchParams } from '../../utils/interns/internListParams'
import { isListBackgroundRefetch, withListDataRefreshingClass } from '../../utils/listPageDataRefreshing'
import { applyTableSortToSearchParams, withClonedSearchParams } from '../../utils/listPageSearchParams'
import '../../styles/interns-list.css'

/**
 * Список студентов: только композиция секций и URL.
 * Таблица, карточки и скелетон — в components/interns/list/.
 */
function InternsListPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const canCreateIntern = canWriteInterviews(user)
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => parseInternListFromSearchParams(searchParams), [searchParams])

  const [importSyncOpen, setImportSyncOpen] = useState(false)
  const [importDatesOpen, setImportDatesOpen] = useState(false)
  const [importSyncFile, setImportSyncFile] = useState<File | null>(null)
  const [importDatesFile, setImportDatesFile] = useState<File | null>(null)
  const [internFiltersExpanded, setInternFiltersExpanded] = useState(false)

  const importSyncTitleId = useId()
  const importDatesTitleId = useId()
  const internFiltersPanelId = useId()

  const hasActiveSemanticFilters = useMeaningfulListFilters(searchParams)

  const {
    directionsQuery,
    managersQuery,
    listQuery,
    deleteMutation,
    syncImport,
    datesImport,
    count,
    totalPages,
    currentPage,
    results,
  } = useInternsList(filters)

  const updateParams = useCallback(
    (mut: (next: URLSearchParams) => void) => {
      setSearchParams(withClonedSearchParams(searchParams, mut), { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const toggleSort = useCallback(
    (field: string) => {
      updateParams((next) => {
        applyTableSortToSearchParams(next, field, 'asc')
      })
    },
    [updateParams],
  )

  const directionOptions = useMemo(
    () =>
      (directionsQuery.data ?? []).map((d) => ({
        value: d.id,
        label: d.name,
      })),
    [directionsQuery.data],
  )

  const managerOptions = useMemo(
    () =>
      (managersQuery.data ?? []).map((m) => ({
        value: m.email,
        label: m.full_name || m.email,
      })),
    [managersQuery.data],
  )

  const isInitialLoad = listQuery.isLoading && !listQuery.data

  const skeletonTableHead = (
    <InternListTableHead filters={filters} onToggleSort={toggleSort} />
  )

  return (
    <div className="page interns-list-page">
      <PageIntroCard title="Управление студентами">
        <p>Список всех студентов, зарегистрированных в системе.</p>
      </PageIntroCard>

      {isInitialLoad ? (
        <InternListSkeleton tableHead={skeletonTableHead} />
      ) : (
        <div key="page-ready" className="interns-page-ready">
          <CollapsibleSection
            sectionId={internFiltersPanelId}
            expanded={internFiltersExpanded}
            onExpandedChange={setInternFiltersExpanded}
            title="Поиск и фильтры"
            headingId="interns-filters-heading"
          >
            <InternFilters
              filters={filters}
              managerOptions={managerOptions}
              directionOptions={directionOptions}
              managersLoading={managersQuery.isLoading}
              directionsLoading={directionsQuery.isLoading}
              onUpdateParams={updateParams}
            />
          </CollapsibleSection>

          {listQuery.isFetching && listQuery.data ? (
            <LoadingLine message="Обновление списка…" />
          ) : null}
          {listQuery.isError ? (
            <InlineError message="Не удалось загрузить студентов. Попробуйте обновить страницу." />
          ) : null}

          {hasActiveSemanticFilters && listQuery.data ? (
            <p className="filter-results-summary interns-filter-summary">
              Найдено студентов: <strong>{count}</strong>
            </p>
          ) : null}

          {canCreateIntern ? (
            <div className="interviews-subsection">
              <PageHeaderActions>
                <Link className="btn-success" to="/interns/new">
                  + Новый студент
                </Link>
                {isAdmin ? (
                  <>
                    <button type="button" className="btn-primary" onClick={() => setImportSyncOpen(true)}>
                      Импорт студентов
                    </button>
                    <button type="button" className="btn-primary" onClick={() => setImportDatesOpen(true)}>
                      Добавить даты выходов на реальные собесы
                    </button>
                  </>
                ) : null}
              </PageHeaderActions>
            </div>
          ) : null}

          {!listQuery.isLoading && !listQuery.isError ? (
            <section
              className={withListDataRefreshingClass(
                'interns-list-section',
                isListBackgroundRefetch(listQuery.isFetching, Boolean(listQuery.data)),
              )}
            >
              {results.length === 0 ? (
                <InternListEmptyState />
              ) : (
                <>
                  <InternListDesktopTable
                    filters={filters}
                    onToggleSort={toggleSort}
                    results={results}
                    isAdmin={isAdmin}
                    onDeleteIntern={(id) => deleteMutation.mutate(id)}
                  />
                  <InternListMobileCards
                    results={results}
                    isAdmin={isAdmin}
                    onDeleteIntern={(id) => deleteMutation.mutate(id)}
                  />
                </>
              )}

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
          ) : null}
        </div>
      )}

      <ImportModal
        open={importSyncOpen}
        title="Импорт студентов"
        description={
          <ul className="import-modal__notes">
            <li>CSV или XLSX из файла (ФИО, направление, город, CV, контакты и др.).</li>
            <li>
              <strong>Не удаляет</strong> существующих студентов и <strong>не затирает</strong> уже
              заполненные поля пустыми значениями из файла.
            </li>
            <li>Дополняет пустые поля и добавляет новых студентов.</li>
          </ul>
        }
        file={importSyncFile}
        onFileChange={setImportSyncFile}
        onExitComplete={() => {
          setImportSyncOpen(false)
          setImportSyncFile(null)
          syncImport.setImportTaskId(null)
        }}
        onSubmit={() => {
          if (importSyncFile) {
            syncImport.importMutation.mutate(importSyncFile)
          }
        }}
        pending={syncImport.importMutation.isPending}
        taskId={syncImport.importTaskId}
        titleId={importSyncTitleId}
      />

      <ImportModal
        open={importDatesOpen}
        title="Импорт дат выхода на реальные собеседования"
        description={
          <ul className="import-modal__notes">
            <li>
              Колонки: <strong>«ФИ»</strong> и <strong>«Дата»</strong>.
            </li>
            <li>Даты в скобках игнорируются.</li>
            <li>Студенты, не найденные в базе, пропускаются.</li>
          </ul>
        }
        file={importDatesFile}
        onFileChange={setImportDatesFile}
        onExitComplete={() => {
          setImportDatesOpen(false)
          setImportDatesFile(null)
          datesImport.setImportTaskId(null)
        }}
        onSubmit={() => {
          if (importDatesFile) {
            datesImport.importMutation.mutate(importDatesFile)
          }
        }}
        pending={datesImport.importMutation.isPending}
        taskId={datesImport.importTaskId}
        titleId={importDatesTitleId}
      />
    </div>
  )
}

export default InternsListPage
