import { useEffect, useRef, useState } from 'react'

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Рубли с целым значением */
function formatRubIntegerDuringAnimation(current: number): string {
  const n = Math.trunc(current)
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  const withSpaces = String(abs).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  return `${sign}${withSpaces} ₽`
}

/** Отображение числа во время анимации */
function formatDuringAnimation(
  current: number,
  format?: 'percent' | 'decimal2' | 'integerRuble',
): string {
  if (format === 'percent') {
    return `${current.toFixed(1)}%`
  }
  if (format === 'decimal2') {
    return current.toFixed(2)
  }
  if (format === 'integerRuble') {
    return formatRubIntegerDuringAnimation(current)
  }
  const rounded = Math.round(current)
  return String(rounded).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

function initialMetricText(
  formatted: string,
  numericTarget: number | null,
  format?: 'percent' | 'decimal2' | 'integerRuble',
): string {
  if (numericTarget == null || !Number.isFinite(numericTarget) || numericTarget < 0) {
    return formatted
  }
  if (prefersReducedMotion()) {
    return formatted
  }
  return formatDuringAnimation(0, format)
}

export interface MetricAnimatedStrongProps {
  /** Итоговая строка из format*MetricValue — в конце анимации совпадает с ней. */
  formatted: string
  /** Число для count-up; null — не число (ФИО менеджера и т.п.). */
  numericTarget: number | null
  format?: 'percent' | 'decimal2' | 'integerRuble'
}

/**
 * Число в метрике: при появлении в viewport — плавная анимация счёта (count-up).
 * Строковые значения и prefers-reduced-motion — только статичный текст.
 * Смена `formatted` / `numericTarget` обрабатывается через `key` на родителе (ремонт).
 */
export function MetricAnimatedStrong({ formatted, numericTarget, format }: MetricAnimatedStrongProps) {
  const ref = useRef<HTMLElement>(null)
  const doneRef = useRef(false)
  const [text, setText] = useState(() => initialMetricText(formatted, numericTarget, format))

  useEffect(() => {
    if (numericTarget == null || !Number.isFinite(numericTarget) || numericTarget < 0) {
      return
    }
    if (prefersReducedMotion()) {
      return
    }

    const el = ref.current
    if (!el) {
      return
    }

    const duration = 700
    let raf = 0

    const runAnimation = () => {
      const start = performance.now()
      const target = numericTarget

      const step = (now: number) => {
        const elapsed = now - start
        const progress = Math.min(elapsed / duration, 1)
        const easeOut = 1 - (1 - progress) ** 2
        const current = easeOut * target
        setText(formatDuringAnimation(current, format))
        if (progress < 1) {
          raf = requestAnimationFrame(step)
        } else {
          setText(formatted)
        }
      }

      raf = requestAnimationFrame(step)
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (!entry?.isIntersecting || doneRef.current) {
          return
        }
        doneRef.current = true
        runAnimation()
      },
      { threshold: 0.2 },
    )

    observer.observe(el)

    return () => {
      observer.disconnect()
      if (raf) {
        cancelAnimationFrame(raf)
      }
    }
  }, [numericTarget, format, formatted])

  return <strong ref={ref}>{text}</strong>
}
