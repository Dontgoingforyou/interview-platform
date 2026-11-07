import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

const VIEWPORT_MARGIN = 12
const TOOLTIP_MAX_WIDTH = 280
/** Оценка высоты тултипа для выбора показа сверху/снизу */
const TOOLTIP_EST_HEIGHT = 88

interface MetricInfoIconProps {
  text: string
}

/** Иконка «i» с тултипом через портал (карточки аналитики). */
function MetricInfoIcon({ text }: MetricInfoIconProps) {
  const [visible, setVisible] = useState(false)
  const [coords, setCoords] = useState<{
    top: number
    left: number
    transform: string
  } | null>(null)
  const ref = useRef<HTMLSpanElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const calcCoords = useCallback(() => {
    if (!ref.current) {
      return null
    }
    const rect = ref.current.getBoundingClientRect()
    const vw = window.innerWidth
    const maxW = Math.min(TOOLTIP_MAX_WIDTH, vw - 2 * VIEWPORT_MARGIN)
    const halfW = maxW / 2
    let centerX = rect.left + rect.width / 2
    centerX = Math.max(VIEWPORT_MARGIN + halfW, Math.min(centerX, vw - VIEWPORT_MARGIN - halfW))

    const spaceAbove = rect.top
    const placeBelow = spaceAbove < TOOLTIP_EST_HEIGHT + VIEWPORT_MARGIN
    const top = placeBelow ? rect.bottom + VIEWPORT_MARGIN : rect.top
    const transform = placeBelow
      ? 'translateX(-50%) translateY(0)'
      : 'translateX(-50%) translateY(calc(-100% - 12px))'

    return { top, left: centerX, transform }
  }, [])

  const show = useCallback(() => {
    const c = calcCoords()
    if (c) {
      setCoords(c)
      setVisible(true)
    }
  }, [calcCoords])

  const hide = useCallback(() => {
    setVisible(false)
  }, [])

  /** Touch-устройства: по tap переключаем видимость вместо hover */
  const handleClick = useCallback(
    (e: React.PointerEvent<HTMLSpanElement>) => {
      if (e.pointerType === 'touch') {
        e.stopPropagation()
        if (visible) {
          hide()
        } else {
          show()
        }
      }
    },
    [visible, show, hide],
  )

  /** Пересчёт позиции при скролле/ресайзе пока тултип открыт */
  useEffect(() => {
    if (!visible) {
      return
    }
    const update = () => {
      const c = calcCoords()
      if (c) {
        setCoords(c)
      }
    }
    window.addEventListener('scroll', update, { passive: true, capture: true })
    window.addEventListener('resize', update, { passive: true })
    return () => {
      window.removeEventListener('scroll', update, { capture: true })
      window.removeEventListener('resize', update)
    }
  }, [visible, calcCoords])

  /** Закрытие по клику/тапу вне иконки и тултипа */
  useEffect(() => {
    if (!visible) {
      return
    }
    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as Node | null
      if (ref.current?.contains(target) || tooltipRef.current?.contains(target)) {
        return
      }
      hide()
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
    }
  }, [visible, hide])

  return (
    <>
      <span
        ref={ref}
        className="metric-info-icon"
        aria-label={text}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        onPointerUp={handleClick}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <path d="M8 6V8M8 10H8.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
      {visible && coords
        ? createPortal(
            <div
              ref={tooltipRef}
              className="metric-info-portal-tooltip"
              style={{ top: coords.top, left: coords.left, transform: coords.transform }}
              role="tooltip"
            >
              {text}
            </div>,
            document.body,
          )
        : null}
    </>
  )
}

export default MetricInfoIcon
