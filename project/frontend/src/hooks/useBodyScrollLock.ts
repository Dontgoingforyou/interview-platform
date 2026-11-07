import { useEffect } from 'react'

/** Замер ширины классической полосы прокрутки (работает при overlay=0 от viewport). */
function measureScrollbarWidthFromElement(): number {
  const outer = document.createElement('div')
  outer.style.cssText = 'position:absolute;left:-9999px;overflow:scroll;width:100px;height:100px;visibility:hidden'
  document.body.appendChild(outer)
  const inner = document.createElement('div')
  inner.style.cssText = 'width:100%;height:200px'
  outer.appendChild(inner)
  const w = outer.offsetWidth - outer.clientWidth
  outer.remove()
  return w > 0 ? w : 0
}

/** Ширина полосы прокрутки: сначала viewport, затем при scrollbar-gutter: stable — замер через временный div. */
function getScrollbarGutterWidth(): number {
  const root = document.documentElement
  const fromViewport = window.innerWidth - root.clientWidth
  if (fromViewport > 0) {
    return fromViewport
  }
  const fromRoot = root.offsetWidth - root.clientWidth
  if (fromRoot > 0) {
    return fromRoot
  }
  const scrollable = root.scrollHeight > window.innerHeight
  if (scrollable) {
    const fromProbe = measureScrollbarWidthFromElement()
    if (fromProbe > 0) {
      return fromProbe
    }
    return 15
  }
  return 0
}

/**
 * Блокирует прокрутку документа и компенсирует исчезновение скроллбара.
 * Padding на html (не на body): иначе при scrollbar-gutter: stable (base.css) контент «плывёт» влево/вправо.
 * layout.css: html[data-scroll-lock] { scrollbar-gutter: auto } — снимает конфликт со stable на время модалки.
 * --scroll-lock-gutter — для position:fixed (переключатель темы).
 */
export function useBodyScrollLock(active: boolean): void {
  useEffect(() => {
    if (!active) {
      return
    }
    const html = document.documentElement
    const body = document.body
    const gutter = getScrollbarGutterWidth()

    const prevHtmlOverflow = html.style.overflow
    const prevBodyOverflow = body.style.overflow
    const prevHtmlPad = html.style.paddingRight
    const prevScrollLockVar = html.style.getPropertyValue('--scroll-lock-gutter')

    html.setAttribute('data-scroll-lock', '')
    html.style.overflow = 'hidden'
    body.style.overflow = 'hidden'
    html.style.setProperty('--scroll-lock-gutter', `${gutter}px`)
    if (gutter > 0) {
      html.style.paddingRight = `${gutter}px`
    }

    return () => {
      html.removeAttribute('data-scroll-lock')
      html.style.overflow = prevHtmlOverflow
      body.style.overflow = prevBodyOverflow
      html.style.paddingRight = prevHtmlPad
      if (prevScrollLockVar) {
        html.style.setProperty('--scroll-lock-gutter', prevScrollLockVar)
      } else {
        html.style.removeProperty('--scroll-lock-gutter')
      }
    }
  }, [active])
}
