import { Fragment, useEffect, useId, useMemo, useState } from 'react'

import { KB_SECTION_DEFAULT_ICON, KB_SECTION_ICON_CHOICES } from '../../constants/kbSectionIcons'
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'

export interface KbSectionFormValues {
  section_id: string
  title: string
  description: string
  icon: string
}

interface KbSectionFormModalProps {
  open: boolean
  onExitComplete: () => void
  variant: 'create' | 'edit'
  title: string
  titleId: string
  initial: KbSectionFormValues
  lockSectionId?: boolean
  submitLabel: string
  onSubmit: (v: KbSectionFormValues) => void
  pending: boolean
}

function normalizeSectionFormInitial(initial: KbSectionFormValues): KbSectionFormValues {
  return {
    ...initial,
    icon: initial.icon?.trim() || KB_SECTION_DEFAULT_ICON,
  }
}

/**
 * Модальное окно создания/редактирования раздела БЗ: поля и выбор иконки сеткой, как в легаси.
 * Состояние формы сбрасывается при смене `key` на родителе.
 */
function KbSectionFormModal(props: KbSectionFormModalProps) {
  const modal = useModalEnterExit(props.open, { onExitComplete: props.onExitComplete })
  useBodyScrollLock(modal.shouldMount)

  const [values, setValues] = useState<KbSectionFormValues>(() => normalizeSectionFormInitial(props.initial))
  const iconGroupId = useId()

  /* Сброс при открытии; initial для «создать» — стабильная константа, для «редактировать» — useMemo на родителе */
  useEffect(() => {
    if (!props.open) {
      return
    }
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- намеренно подтягиваем initial при открытии */
    setValues(normalizeSectionFormInitial(props.initial))
  }, [props.open, props.initial])

  const iconChoicesForUi = useMemo(() => {
    const cur = values.icon
    const standard = [...KB_SECTION_ICON_CHOICES] as string[]
    if (cur && !standard.includes(cur)) {
      return [cur, ...standard]
    }
    return standard
  }, [values.icon])

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    props.onSubmit({
      ...values,
      icon: values.icon.trim() || KB_SECTION_DEFAULT_ICON,
    })
  }

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
      <div
        className="kb-modal kb-modal--section"
        role="dialog"
        aria-modal
        aria-labelledby={props.titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="kb-modal-header">
          <h2 id={props.titleId} className="kb-modal-title">
            {props.title}
          </h2>
          <button
            type="button"
            className="kb-modal-close"
            onClick={() => {
              if (!props.pending) {
                modal.requestClose()
              }
            }}
            title="Закрыть"
          >
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="kb-modal-body">
            <div className="kb-form-group">
              <label className="kb-form-label" htmlFor={`${iconGroupId}-section-id`}>
                ID раздела (латиница, цифры, дефис)
              </label>
              <input
                id={`${iconGroupId}-section-id`}
                className="form-control"
                value={values.section_id}
                disabled={props.lockSectionId}
                onChange={(e) => setValues((s) => ({ ...s, section_id: e.target.value }))}
                pattern="[a-z0-9\-]+"
                placeholder="например: new-section"
                required={!props.lockSectionId}
              />
              {!props.lockSectionId && <small className="kb-form-hint">Будет использоваться в URL</small>}
            </div>
            <div className="kb-form-group">
              <label className="kb-form-label" htmlFor={`${iconGroupId}-title`}>
                Название раздела
              </label>
              <input
                id={`${iconGroupId}-title`}
                className="form-control"
                value={values.title}
                onChange={(e) => setValues((s) => ({ ...s, title: e.target.value }))}
                placeholder="Название"
                required
              />
            </div>
            <div className="kb-form-group">
              <label className="kb-form-label" htmlFor={`${iconGroupId}-desc`}>
                Описание
              </label>
              <textarea
                id={`${iconGroupId}-desc`}
                className="form-control"
                rows={3}
                value={values.description}
                onChange={(e) => setValues((s) => ({ ...s, description: e.target.value }))}
                placeholder="Краткое описание раздела"
              />
            </div>
            <div className="kb-form-group">
              <span className="kb-form-label" id={`${iconGroupId}-icon-label`}>
                Выберите иконку
              </span>
              <div
                className="kb-icon-selector"
                role="radiogroup"
                aria-labelledby={`${iconGroupId}-icon-label`}
              >
                {iconChoicesForUi.map((emoji, i) => {
                  const inputId = `${iconGroupId}-icon-${props.variant}-${i}`
                  return (
                    <Fragment key={`${emoji}-${i}`}>
                      <input
                        type="radio"
                        name={`kb-section-icon-${props.variant}`}
                        id={inputId}
                        value={emoji}
                        checked={values.icon === emoji}
                        onChange={() => setValues((s) => ({ ...s, icon: emoji }))}
                        className="kb-icon-selector-input"
                      />
                      <label htmlFor={inputId} className="kb-icon-option">
                        {emoji}
                      </label>
                    </Fragment>
                  )
                })}
              </div>
            </div>
          </div>
          <div className="kb-modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              disabled={props.pending}
              onClick={() => modal.requestClose()}
            >
              Отмена
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                props.pending ||
                !values.title.trim() ||
                (!props.lockSectionId && !values.section_id.trim())
              }
            >
              {props.submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default KbSectionFormModal
