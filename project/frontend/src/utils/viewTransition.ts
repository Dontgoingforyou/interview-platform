/** Обёртка для document.startViewTransition с учётом prefers-reduced-motion и отсутствия API. */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function runWithViewTransition(updateDom: () => void): void {
  if (prefersReducedMotion()) {
    updateDom()
    return
  }
  const doc = document as Document & { startViewTransition?: (cb: () => void) => ViewTransition }
  if (typeof doc.startViewTransition !== 'function') {
    updateDom()
    return
  }
  doc.startViewTransition(updateDom)
}
