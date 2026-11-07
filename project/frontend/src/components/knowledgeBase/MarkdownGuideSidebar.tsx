import { useEffect } from 'react'

import { MARKDOWN_GUIDE_SECTIONS } from './markdownGuideSections'

interface MarkdownGuideSidebarProps {
  open: boolean
  onClose: () => void
}

/**
 * Боковая панель со справкой по Markdown (аналог легаси markdown_guide.html).
 */
function MarkdownGuideSidebar({ open, onClose }: MarkdownGuideSidebarProps) {
  useEffect(() => {
    if (!open) {
      return
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <>
      <div
        role="presentation"
        className={
          open ? 'kb-markdown-guide-overlay kb-markdown-guide-overlay--visible' : 'kb-markdown-guide-overlay'
        }
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside
        className={
          open ? 'kb-markdown-guide-sidebar kb-markdown-guide-sidebar--open' : 'kb-markdown-guide-sidebar'
        }
        aria-hidden={!open}
        id="kb-markdown-guide-panel"
      >
        <div className="kb-markdown-guide-header">
          <h3 className="kb-markdown-guide-title">📖 Полный гайд по Markdown</h3>
          <button type="button" className="kb-markdown-guide-close" onClick={onClose} title="Закрыть">
            ✕
          </button>
        </div>
        <div className="kb-markdown-guide-content">
          {MARKDOWN_GUIDE_SECTIONS.map((section) => (
            <div key={section.title} className="kb-guide-section">
              <h4 className="kb-guide-section__title">{section.title}</h4>
              <pre className="kb-guide-section__code">{section.code}</pre>
              {section.hint ? <small className="kb-guide-section__hint">{section.hint}</small> : null}
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}

export default MarkdownGuideSidebar
