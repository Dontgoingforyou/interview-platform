import { useCallback, useLayoutEffect, useRef, useState, type ReactNode } from 'react'

interface TableScrollProps {
  children: ReactNode
  className?: string
}

/** Горизонтальный скролл + оформление для `.data-table`; сверху — синхронная полоса прокрутки. */
function TableScroll({ children, className }: TableScrollProps) {
  const mainRef = useRef<HTMLDivElement>(null)
  const topRef = useRef<HTMLDivElement>(null)
  const sizerRef = useRef<HTMLDivElement>(null)
  const [hScrolled, setHScrolled] = useState(false)
  const [showTopRail, setShowTopRail] = useState(false)

  const isPlain = Boolean(className?.includes('table-scroll--plain'))

  const syncHorizontalScrolled = useCallback(() => {
    const main = mainRef.current
    if (!main) {
      return
    }
    const next = main.scrollLeft > 0
    setHScrolled((prev) => (prev === next ? prev : next))
  }, [])

  const measure = useCallback(() => {
    const main = mainRef.current
    const sizer = sizerRef.current
    if (!main || !sizer) {
      return
    }
    sizer.style.width = `${main.scrollWidth}px`
    const overflow = main.scrollWidth > main.clientWidth + 2
    setShowTopRail((prev) => (prev === overflow ? prev : overflow))
  }, [])

  const onMainScroll = useCallback(() => {
    const main = mainRef.current
    const top = topRef.current
    if (top && main && top.scrollLeft !== main.scrollLeft) {
      top.scrollLeft = main.scrollLeft
    }
    syncHorizontalScrolled()
  }, [syncHorizontalScrolled])

  const onTopScroll = useCallback(() => {
    const main = mainRef.current
    const top = topRef.current
    if (top && main && main.scrollLeft !== top.scrollLeft) {
      main.scrollLeft = top.scrollLeft
    }
    syncHorizontalScrolled()
  }, [syncHorizontalScrolled])

  useLayoutEffect(() => {
    const main = mainRef.current
    if (!main) {
      return undefined
    }

    const ro = new ResizeObserver(() => measure())
    const observeContent = () => {
      ro.disconnect()
      ro.observe(main)
      const table = main.querySelector('table')
      if (table) {
        ro.observe(table)
      }
    }
    observeContent()

    const mo = new MutationObserver(() => {
      observeContent()
      measure()
    })
    mo.observe(main, { childList: true, subtree: true })

    main.addEventListener('scroll', onMainScroll, { passive: true })
    window.addEventListener('resize', measure)

    measure()
    syncHorizontalScrolled()

    return () => {
      mo.disconnect()
      ro.disconnect()
      main.removeEventListener('scroll', onMainScroll)
      window.removeEventListener('resize', measure)
    }
  }, [measure, onMainScroll, syncHorizontalScrolled])

  const mainCls = ['table-scroll', hScrolled && 'table-scroll--h-scrolled', className].filter(Boolean).join(' ')
  const railCls = [
    'table-scroll-dual__rail',
    isPlain && 'table-scroll-dual__rail--plain',
    !showTopRail && 'table-scroll-dual__rail--hidden',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="table-scroll-dual">
      <div
        ref={topRef}
        className={railCls}
        aria-hidden="true"
        onScroll={onTopScroll}
      >
        <div ref={sizerRef} className="table-scroll-dual__sizer" />
      </div>
      <div ref={mainRef} className={mainCls}>
        {children}
      </div>
    </div>
  )
}

export default TableScroll
