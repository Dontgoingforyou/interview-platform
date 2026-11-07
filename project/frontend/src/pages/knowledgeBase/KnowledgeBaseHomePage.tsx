import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useId, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import {
  createKbSection,
  deleteKbSection,
  deleteKbArticle,
  updateKbSection,
} from '../../api/knowledgeBaseApi'
import { postSemanticSearch } from '../../api/vectorSearchApi'
import KbSectionFormModal from '../../components/knowledgeBase/KbSectionFormModal'
import type { KbSectionFormValues } from '../../components/knowledgeBase/KbSectionFormModal'
import { KB_SECTION_DEFAULT_ICON } from '../../constants/kbSectionIcons'
import { InlineError, LoadingLine, PageIntroCard } from '../../components/ui'
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'
import {
  kbQueryKeys,
  useKbArticlesQuery,
  useKbFullTextSearchQuery,
  useKbSectionsQuery,
} from '../../hooks/knowledgeBase/useKnowledgeBaseQueries'
import { useAuthStore } from '../../store/authStore'
import type { KbSection, SemanticSearchResultItem } from '../../types/knowledgeBase'
import { isAdminUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'
import { kbArticleNewPath, kbArticlePath } from './kbPaths'

type SearchMode = 'text' | 'semantic'

const KB_CREATE_INITIAL: KbSectionFormValues = {
  section_id: '',
  title: '',
  description: '',
  icon: KB_SECTION_DEFAULT_ICON,
}

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Главная базы знаний: разделы, список статей, полнотекстовый и семантический поиск.
 */
function KnowledgeBaseHomePage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [expandedSectionId, setExpandedSectionId] = useState<string | null>(null)
  const [articlesPanelLeaving, setArticlesPanelLeaving] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const [searchMode, setSearchMode] = useState<SearchMode>('text')
  const [semanticQ, setSemanticQ] = useState('')
  const [semanticHits, setSemanticHits] = useState<SemanticSearchResultItem[] | null>(null)
  const [semanticLoading, setSemanticLoading] = useState(false)
  const [semanticError, setSemanticError] = useState<string | null>(null)

  const [createOpen, setCreateOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<KbSection | null>(null)
  const [editOpen, setEditOpen] = useState(false)

  const [deleteSectionDialog, setDeleteSectionDialog] = useState<KbSection | null>(null)
  const [deleteSectionOpen, setDeleteSectionOpen] = useState(false)
  const [deleteArticleDialog, setDeleteArticleDialog] = useState<{
    sectionId: string
    filename: string
    title: string
  } | null>(null)
  const [deleteArticleOpen, setDeleteArticleOpen] = useState(false)

  const createModalTitleId = useId()
  const debouncedQ = useDebouncedValue(searchQ.trim(), 300)
  const debouncedSemanticQ = useDebouncedValue(semanticQ.trim(), 300)

  const sectionsQuery = useKbSectionsQuery()
  const articlesQuery = useKbArticlesQuery(expandedSectionId ?? undefined)
  const textSearchQuery = useKbFullTextSearchQuery(debouncedQ)

  const sectionFromUrl = searchParams.get('section')
  /* Синхронизация открытого раздела с ?section= из URL */
  /* eslint-disable react-hooks/set-state-in-effect -- инициализация из searchParams после загрузки списка */
  useEffect(() => {
    if (sectionFromUrl && sectionsQuery.data?.some((s) => s.id === sectionFromUrl)) {
      setArticlesPanelLeaving(false)
      setExpandedSectionId(sectionFromUrl)
    }
  }, [sectionFromUrl, sectionsQuery.data])
  /* eslint-enable react-hooks/set-state-in-effect */

  const expandedSection = useMemo(
    () => sectionsQuery.data?.find((s) => s.id === expandedSectionId) ?? null,
    [sectionsQuery.data, expandedSectionId],
  )

  const openSection = useCallback(
    (id: string) => {
      setArticlesPanelLeaving(false)
      setExpandedSectionId(id)
      setSearchParams({ section: id }, { replace: true })
    },
    [setSearchParams],
  )

  const finishCloseSection = useCallback(() => {
    setArticlesPanelLeaving(false)
    setExpandedSectionId(null)
    setSearchParams({}, { replace: true })
  }, [setSearchParams])

  const closeSection = useCallback(() => {
    if (!expandedSectionId) {
      return
    }
    if (prefersReducedMotion()) {
      finishCloseSection()
      return
    }
    setArticlesPanelLeaving(true)
  }, [expandedSectionId, finishCloseSection])

  useEffect(() => {
    if (!articlesPanelLeaving) {
      return
    }
    if (!prefersReducedMotion()) {
      return
    }
    const id = window.requestAnimationFrame(() => {
      finishCloseSection()
    })
    return () => window.cancelAnimationFrame(id)
  }, [articlesPanelLeaving, finishCloseSection])

  const handleArticlesPanelAnimationEnd = useCallback(
    (e: React.AnimationEvent<HTMLElement>) => {
      if (e.target !== e.currentTarget) {
        return
      }
      if (!articlesPanelLeaving) {
        return
      }
      if (!String(e.animationName).includes('kb-slide-up-leave')) {
        return
      }
      finishCloseSection()
    },
    [articlesPanelLeaving, finishCloseSection],
  )

  const invalidateKb = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: kbQueryKeys.sections })
  }, [queryClient])

  const createSectionMutation = useMutation({
    mutationFn: (payload: { section_id: string; title: string; description: string; icon: string }) =>
      createKbSection(payload),
    onSuccess: () => {
      toast.success('Раздел создан')
      setCreateOpen(false)
      invalidateKb()
    },
    onError: () => toast.error('Не удалось создать раздел'),
  })

  const updateSectionMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string
      payload: { title?: string; description?: string; icon?: string }
    }) => updateKbSection(id, payload),
    onSuccess: () => {
      toast.success('Раздел обновлён')
      setEditOpen(false)
      invalidateKb()
    },
    onError: () => toast.error('Не удалось обновить раздел'),
  })

  const deleteSectionMutation = useMutation({
    mutationFn: (id: string) => deleteKbSection(id),
    onSuccess: (_data, deletedId) => {
      toast.success('Раздел удалён')
      setDeleteSectionOpen(false)
      if (expandedSectionId === deletedId) {
        if (prefersReducedMotion()) {
          finishCloseSection()
        } else {
          setArticlesPanelLeaving(true)
        }
      }
      invalidateKb()
    },
    onError: () => toast.error('Не удалось удалить раздел'),
  })

  const deleteArticleMutation = useMutation({
    mutationFn: ({ sectionId, filename }: { sectionId: string; filename: string }) =>
      deleteKbArticle(sectionId, filename),
    onSuccess: () => {
      toast.success('Статья удалена')
      setDeleteArticleOpen(false)
      void queryClient.invalidateQueries({ queryKey: kbQueryKeys.articles(expandedSectionId ?? '') })
      invalidateKb()
    },
    onError: () => toast.error('Не удалось удалить статью'),
  })

  /* Семантический поиск по дебаунсу (аналог полнотекстового); сброс состояния при пустом запросе */
  /* eslint-disable react-hooks/set-state-in-effect -- побочные эффекты запроса и очистки результата */
  useEffect(() => {
    if (searchMode !== 'semantic') {
      return
    }
    if (!debouncedSemanticQ) {
      setSemanticHits(null)
      setSemanticError(null)
      setSemanticLoading(false)
      return
    }

    let cancelled = false
    setSemanticLoading(true)
    setSemanticError(null)
    setSemanticHits(null)

    void postSemanticSearch({ query: debouncedSemanticQ, entity_type: 'kb_article', top_k: 20 })
      .then((data) => {
        if (!cancelled) {
          setSemanticHits(data.results)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSemanticError('Семантический поиск недоступен или произошла ошибка.')
          setSemanticHits([])
        }
      })
      .finally(() => {
        if (!cancelled) {
          setSemanticLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [searchMode, debouncedSemanticQ])
  /* eslint-enable react-hooks/set-state-in-effect */

  const resolveSemanticLink = useCallback((row: SemanticSearchResultItem) => {
    const meta = row.metadata
    const rawSid = meta.section_id
    const rawFn = meta.filename
    const sid = rawSid != null && rawSid !== '' ? String(rawSid) : null
    const fn = rawFn != null && rawFn !== '' ? String(rawFn) : null
    if (!sid || !fn) {
      return null
    }
    return kbArticlePath(sid, fn)
  }, [])

  const editFormInitial = useMemo<KbSectionFormValues>(
    () =>
      editTarget
        ? {
            section_id: editTarget.id,
            title: editTarget.title,
            description: editTarget.description,
            icon: editTarget.icon,
          }
        : KB_CREATE_INITIAL,
    [editTarget],
  )

  const openEditSection = useCallback((section: KbSection) => {
    setEditTarget(section)
    setEditOpen(true)
  }, [])

  const openDeleteSection = useCallback((section: KbSection) => {
    setDeleteSectionDialog(section)
    setDeleteSectionOpen(true)
  }, [])

  const openDeleteArticle = useCallback(
    (payload: { sectionId: string; filename: string; title: string }) => {
      setDeleteArticleDialog(payload)
      setDeleteArticleOpen(true)
    },
    [],
  )

  return (
    <div className="kb-page">
      <PageIntroCard title="О разделе">
        Разделы со статьями в формате Markdown. Полнотекстовый поиск по заголовку и тексту; семантический — по
        смыслу.
      </PageIntroCard>

      <div className="kb-header-row">
        <div className="kb-search-block">
          <div className="kb-search-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={searchMode === 'text'}
              className={searchMode === 'text' ? 'kb-tab kb-tab-active' : 'kb-tab'}
              onClick={() => setSearchMode('text')}
            >
              Поиск по тексту
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={searchMode === 'semantic'}
              className={searchMode === 'semantic' ? 'kb-tab kb-tab-active' : 'kb-tab'}
              onClick={() => setSearchMode('semantic')}
            >
              Семантический поиск
            </button>
          </div>
          {searchMode === 'text' ? (
            <div className="kb-search-field-wrap">
              <input
                type="search"
                className="form-control kb-search-input"
                placeholder="Поиск по базе знаний…"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                aria-label="Полнотекстовый поиск"
              />
              {debouncedQ.length > 0 && (
                <div className="kb-search-dropdown">
                  {textSearchQuery.isFetching && <LoadingLine message="Поиск…" />}
                  {textSearchQuery.isError && <InlineError message="Ошибка поиска" />}
                  {textSearchQuery.data && textSearchQuery.data.length === 0 && (
                    <p className="kb-muted">Ничего не найдено</p>
                  )}
                  {textSearchQuery.data?.map((hit) => (
                    <Link
                      key={`${hit.section_id}-${hit.filename}`}
                      className="kb-search-hit"
                      to={kbArticlePath(hit.section_id, hit.filename)}
                    >
                      <span className="kb-search-hit-icon">{hit.section_icon}</span>
                      <span>
                        <strong>{hit.title}</strong>
                        <span className="kb-muted"> — {hit.section_title}</span>
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="kb-search-field-wrap">
              <input
                type="search"
                className="form-control kb-search-input"
                placeholder="Запрос на естественном языке…"
                value={semanticQ}
                onChange={(e) => setSemanticQ(e.target.value)}
                aria-label="Семантический поиск"
              />
            </div>
          )}
        </div>
      </div>

      {searchMode === 'semantic' && semanticError && <InlineError message={semanticError} />}
      {searchMode === 'semantic' && semanticLoading && <LoadingLine message="Семантический поиск…" />}
      {searchMode === 'semantic' && semanticHits && semanticHits.length > 0 && (
        <ul className="kb-semantic-list list-unstyled">
          {semanticHits.map((row) => {
            const to = resolveSemanticLink(row)
            const title =
              (typeof row.metadata.title === 'string' && row.metadata.title) || row.text_content.slice(0, 80)
            return (
              <li key={`${row.entity_type}-${row.entity_id}`} className="kb-semantic-item">
                {to ? (
                  <Link to={to}>
                    {title}
                    <span className="kb-muted"> — score {(row.similarity_score * 100).toFixed(0)}%</span>
                  </Link>
                ) : (
                  <span>
                    {title}
                    <span className="kb-muted"> — нет ссылки (нет section_id/filename в метаданных)</span>
                  </span>
                )}
              </li>
            )
          })}
        </ul>
      )}
      {searchMode === 'semantic' &&
        semanticHits &&
        semanticHits.length === 0 &&
        !semanticLoading &&
        !semanticError && (
          <p className="kb-muted">
            Нет результатов. Убедитесь, что статьи проиндексированы (команда vectorize_data на сервере).
          </p>
        )}

      {sectionsQuery.isLoading && <LoadingLine message="Загрузка разделов…" />}
      {sectionsQuery.isError && <InlineError message="Не удалось загрузить разделы" />}
      {sectionsQuery.data && (
        <div className="kb-sections-grid">
          {sectionsQuery.data.map((section) => (
            <div
              key={section.id}
              role="button"
              tabIndex={0}
              className={
                expandedSectionId === section.id ? 'kb-section-card kb-section-card-active' : 'kb-section-card'
              }
              onClick={() => openSection(section.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  openSection(section.id)
                }
              }}
            >
              {isAdmin && (
                <div className="kb-section-card-admin">
                  <button
                    type="button"
                    className="kb-icon-btn kb-icon-btn--edit"
                    onClick={(e) => {
                      e.stopPropagation()
                      openEditSection(section)
                    }}
                    title="Редактировать раздел"
                  >
                    ✏️
                  </button>
                  <button
                    type="button"
                    className="kb-icon-btn kb-icon-btn--delete"
                    onClick={(e) => {
                      e.stopPropagation()
                      openDeleteSection(section)
                    }}
                    title="Удалить раздел"
                  >
                    🗑️
                  </button>
                </div>
              )}
              <span className="kb-section-icon" aria-hidden>
                {section.icon}
              </span>
              <div className="kb-section-card-body">
                <h3 className="kb-section-title">{section.title}</h3>
                <p className="kb-section-desc">{section.description || '—'}</p>
                <span className="kb-section-count">
                  {section.article_count}{' '}
                  {section.article_count === 1 ? 'статья' : section.article_count < 5 ? 'статьи' : 'статей'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {isAdmin && (
        <button type="button" className="btn btn-secondary kb-btn-create-section" onClick={() => setCreateOpen(true)}>
          ➕ Создать раздел
        </button>
      )}

      {expandedSectionId && expandedSection && (
        <section
          className={
            articlesPanelLeaving
              ? 'kb-articles-panel kb-articles-panel--leaving'
              : 'kb-articles-panel'
          }
          aria-labelledby="kb-articles-heading"
          onAnimationEnd={handleArticlesPanelAnimationEnd}
        >
          <div key={expandedSectionId} className="kb-articles-panel-inner">
            <div className="kb-articles-panel-head">
              <div>
                <h2 id="kb-articles-heading">{expandedSection.title}</h2>
                <p className="kb-muted">{expandedSection.description}</p>
              </div>
              <div className="kb-articles-panel-actions">
                {isAdmin && (
                  <Link className="btn btn-primary btn-small" to={kbArticleNewPath(expandedSectionId)}>
                    ➕ Создать статью
                  </Link>
                )}
                <button type="button" className="btn btn-secondary btn-small" onClick={closeSection}>
                  Закрыть
                </button>
              </div>
            </div>
            {articlesQuery.isLoading && <LoadingLine message="Загрузка статей…" />}
            {articlesQuery.isError && <InlineError message="Не удалось загрузить статьи" />}
            <ul className="kb-articles-list list-unstyled">
              {articlesQuery.data?.map((a) => (
                <li key={a.filename} className="kb-article-list-item">
                  <div className="kb-article-card">
                    <Link
                      className="kb-article-card-link"
                      to={kbArticlePath(expandedSectionId, a.filename)}
                    >
                      <h3 className="kb-article-card-title">{a.title}</h3>
                    </Link>
                    {isAdmin && (
                      <div className="kb-article-card-footer">
                        <Link
                          className="btn-outline-primary btn-small"
                          to={`/knowledge-base/${encodeURIComponent(expandedSectionId)}/article/${encodeURIComponent(a.filename)}/edit`}
                        >
                          Редактировать
                        </Link>
                        <button
                          type="button"
                          className="btn-outline-danger btn-small"
                          onClick={() =>
                            openDeleteArticle({
                              sectionId: expandedSectionId,
                              filename: a.filename,
                              title: a.title,
                            })
                          }
                        >
                          Удалить
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <KbSectionFormModal
        key="kb-section-create"
        open={createOpen}
        onExitComplete={() => setCreateOpen(false)}
        variant="create"
        titleId={createModalTitleId}
        title="Создать новый раздел"
        initial={KB_CREATE_INITIAL}
        submitLabel="Создать"
        onSubmit={(values) =>
          createSectionMutation.mutate({
            section_id: values.section_id.trim(),
            title: values.title.trim(),
            description: values.description.trim(),
            icon: values.icon.trim() || KB_SECTION_DEFAULT_ICON,
          })
        }
        pending={createSectionMutation.isPending}
      />

      <KbSectionFormModal
        key={editTarget ? `kb-section-edit-${editTarget.id}` : 'kb-section-edit-idle'}
        open={editOpen}
        onExitComplete={() => {
          setEditOpen(false)
          setEditTarget(null)
        }}
        variant="edit"
        titleId={createModalTitleId}
        title="Редактировать раздел"
        initial={editFormInitial}
        lockSectionId
        submitLabel="Сохранить"
        onSubmit={(values) => {
          if (!editTarget) {
            return
          }
          updateSectionMutation.mutate({
            id: editTarget.id,
            payload: {
              title: values.title.trim(),
              description: values.description.trim(),
              icon: values.icon.trim() || KB_SECTION_DEFAULT_ICON,
            },
          })
        }}
        pending={updateSectionMutation.isPending}
      />

      <KbConfirmModal
        open={deleteSectionOpen}
        onExitComplete={() => {
          setDeleteSectionOpen(false)
          setDeleteSectionDialog(null)
        }}
        message={
          deleteSectionDialog
            ? `Удалить раздел «${deleteSectionDialog.title}» и все статьи?`
            : ''
        }
        confirmLabel="Удалить"
        onConfirm={() => {
          if (deleteSectionDialog) {
            deleteSectionMutation.mutate(deleteSectionDialog.id)
          }
        }}
        pending={deleteSectionMutation.isPending}
      />

      <KbConfirmModal
        open={deleteArticleOpen}
        onExitComplete={() => {
          setDeleteArticleOpen(false)
          setDeleteArticleDialog(null)
        }}
        message={
          deleteArticleDialog ? `Удалить статью «${deleteArticleDialog.title}»?` : ''
        }
        confirmLabel="Удалить"
        onConfirm={() => {
          if (deleteArticleDialog) {
            deleteArticleMutation.mutate({
              sectionId: deleteArticleDialog.sectionId,
              filename: deleteArticleDialog.filename,
            })
          }
        }}
        pending={deleteArticleMutation.isPending}
      />
    </div>
  )
}

function KbConfirmModal(props: {
  open: boolean
  onExitComplete: () => void
  message: string
  confirmLabel: string
  onConfirm: () => void
  pending: boolean
}) {
  const modal = useModalEnterExit(props.open, { onExitComplete: props.onExitComplete })
  useBodyScrollLock(modal.shouldMount)

  useEffect(() => {
    if (!modal.shouldMount) {
      return
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !props.pending) {
        modal.requestClose()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [modal, modal.shouldMount, props.pending])

  if (!modal.shouldMount) {
    return null
  }

  return (
    <div
      className={`kb-modal-backdrop ${modal.overlayOpenClass}`}
      role="presentation"
      onClick={() => {
        if (!props.pending) {
          modal.requestClose()
        }
      }}
    >
      <div className="kb-modal kb-modal-sm" role="dialog" aria-modal onClick={(e) => e.stopPropagation()}>
        <p>{props.message}</p>
        <div className="kb-modal-footer">
          <button
            type="button"
            className="btn btn-secondary"
            disabled={props.pending}
            onClick={() => modal.requestClose()}
          >
            Отмена
          </button>
          <button type="button" className="btn btn-danger" disabled={props.pending} onClick={props.onConfirm}>
            {props.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default KnowledgeBaseHomePage
