import { useEffect, useSyncExternalStore, type MutableRefObject, type RefObject } from 'react'

const INTERACTIVE_THEMES = new Set(['winter', 'spring', 'autumn'])

function subscribeTheme(onStoreChange: () => void) {
  const el = document.documentElement
  const mo = new MutationObserver(onStoreChange)
  mo.observe(el, { attributes: true, attributeFilter: ['data-theme'] })
  return () => mo.disconnect()
}

function getThemeSnapshot() {
  return document.documentElement.dataset.theme ?? ''
}

function subscribeReducedMotion(onStoreChange: () => void) {
  if (typeof window === 'undefined') {
    return () => {}
  }
  const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  mq.addEventListener('change', onStoreChange)
  return () => mq.removeEventListener('change', onStoreChange)
}

function getReducedMotionSnapshot() {
  if (typeof window === 'undefined') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Текущее значение data-theme на documentElement (для сезонных эффектов). */
export function useDocumentTheme() {
  return useSyncExternalStore(subscribeTheme, getThemeSnapshot, () => '')
}

export function useReducedMotionPreference() {
  return useSyncExternalStore(subscribeReducedMotion, getReducedMotionSnapshot, () => false)
}

export function isWeatherInteractiveTheme(theme: string) {
  return INTERACTIVE_THEMES.has(theme)
}

const K_PARALLAX = 0.12
const K_GUST = 0.32
const GUST_DECAY = 0.92
const GUST_DISPLAY_SMOOTH = 0.22
const RAIN_WIND_FACTOR = 0.022
const RAIN_WIND_SMOOTH = 0.14

/** Сглаживание смещения частиц к целевому (0..1 за кадр) — без «телепорта» при движении мыши */
const PARTICLE_SMOOTH = 0.16

/** Гауссово влияние курсора без обрыва на границе радиуса */
const SNOW_GAUSS_SIGMA_PX = 100
const SNOW_REPULSE_MAX_PX = 11
const SNOW_ATTRACT = 0.045

const PETAL_GAUSS_SIGMA_PX = 110
const PETAL_REPULSE_MAX_PX = 10
const PETAL_ATTRACT = 0.055

function clearLayerTransforms(
  motionRef: RefObject<HTMLDivElement | null>,
  rainWindRef: RefObject<HTMLDivElement | null>,
  snowBodyRefs: MutableRefObject<(HTMLSpanElement | null)[]>,
  petalBodyRefs: MutableRefObject<(HTMLSpanElement | null)[]>,
) {
  if (motionRef.current) {
    motionRef.current.style.transform = ''
  }
  if (rainWindRef.current) {
    rainWindRef.current.style.transform = ''
  }
  for (const el of snowBodyRefs.current) {
    if (el) {
      el.style.transform = ''
    }
  }
  for (const el of petalBodyRefs.current) {
    if (el) {
      el.style.transform = ''
    }
  }
}

/**
 * Параллакс и порыв ветра на motion-слое, ветер по X для дождя, смещение снежинок и лепестков от курсора.
 * Вызывать только когда тема winter/spring/autumn и не prefers-reduced-motion.
 */
export function useWeatherInteractiveMotion(
  active: boolean,
  motionRef: RefObject<HTMLDivElement | null>,
  rainWindRef: RefObject<HTMLDivElement | null>,
  snowBodyRefs: MutableRefObject<(HTMLSpanElement | null)[]>,
  petalBodyRefs: MutableRefObject<(HTMLSpanElement | null)[]>,
  snowLeftPct: readonly number[],
  petalLeftPct: readonly number[],
) {
  useEffect(() => {
    if (!active) {
      clearLayerTransforms(motionRef, rainWindRef, snowBodyRefs, petalBodyRefs)
      return
    }

    let rafId = 0
    let lastScrollY = window.scrollY
    let gustY = 0
    let gustDisplayY = 0
    let mouseX = -99999
    let rainWindSmoothX = 0

    const snowSmoothX = new Float32Array(snowLeftPct.length)
    const petalSmoothX = new Float32Array(petalLeftPct.length)

    const onScroll = () => {
      const y = window.scrollY
      const d = y - lastScrollY
      lastScrollY = y
      gustY += d * K_GUST
    }

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX
    }

    const gaussianFalloff = (dx: number, sigma: number) => {
      const s = sigma > 1e-6 ? sigma : 1
      return Math.exp(-(dx * dx) / (2 * s * s))
    }

    /**
     * Целевое смещение по X: у оси курсора без рывка (repulse нарастает с |dx|),
     * слабое притяжение к вертикали курсора.
     */
    const targetNudgeSnow = (pxCol: number) => {
      const dx = mouseX - pxCol
      const g = gaussianFalloff(dx, SNOW_GAUSS_SIGMA_PX)
      if (g < 1e-4) {
        return 0
      }
      const adx = Math.abs(dx)
      const repulseRamp = Math.min(1, adx / 32) ** 2
      const repulse =
        adx < 0.5 ? 0 : (-Math.sign(dx) * SNOW_REPULSE_MAX_PX * g * repulseRamp)
      const attract = dx * SNOW_ATTRACT * g
      return repulse + attract
    }

    const targetNudgePetal = (pxCol: number) => {
      const dx = mouseX - pxCol
      const g = gaussianFalloff(dx, PETAL_GAUSS_SIGMA_PX)
      if (g < 1e-4) {
        return 0
      }
      const adx = Math.abs(dx)
      const repulseRamp = Math.min(1, adx / 34) ** 2
      const repulse =
        adx < 0.5 ? 0 : (-Math.sign(dx) * PETAL_REPULSE_MAX_PX * g * repulseRamp)
      const attract = dx * PETAL_ATTRACT * g
      return repulse + attract
    }

    const tick = () => {
      const w = window.innerWidth
      const scrollY = window.scrollY

      gustY *= GUST_DECAY
      if (Math.abs(gustY) < 0.04) {
        gustY = 0
      }

      gustDisplayY += (gustY - gustDisplayY) * GUST_DISPLAY_SMOOTH

      const ty = -scrollY * K_PARALLAX + gustDisplayY
      if (motionRef.current) {
        motionRef.current.style.transform = `translate3d(0, ${ty}px, 0)`
      }

      const windTargetX = (mouseX - w * 0.5) * RAIN_WIND_FACTOR
      rainWindSmoothX += (windTargetX - rainWindSmoothX) * RAIN_WIND_SMOOTH
      if (rainWindRef.current) {
        rainWindRef.current.style.transform = `translate3d(${rainWindSmoothX}px, 0, 0)`
      }

      for (let i = 0; i < snowLeftPct.length; i++) {
        const el = snowBodyRefs.current[i]
        if (!el) {
          continue
        }
        const px = (snowLeftPct[i] / 100) * w
        const target = targetNudgeSnow(px)
        snowSmoothX[i] += (target - snowSmoothX[i]) * PARTICLE_SMOOTH
        el.style.transform = `translate3d(${snowSmoothX[i]}px, 0, 0)`
      }

      for (let i = 0; i < petalLeftPct.length; i++) {
        const el = petalBodyRefs.current[i]
        if (!el) {
          continue
        }
        const px = (petalLeftPct[i] / 100) * w
        const target = targetNudgePetal(px)
        petalSmoothX[i] += (target - petalSmoothX[i]) * PARTICLE_SMOOTH
        el.style.transform = `translate3d(${petalSmoothX[i]}px, 0, 0)`
      }

      rafId = window.requestAnimationFrame(tick)
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('mousemove', onMove, { passive: true })
    lastScrollY = window.scrollY
    rafId = window.requestAnimationFrame(tick)

    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('mousemove', onMove)
      window.cancelAnimationFrame(rafId)
      clearLayerTransforms(motionRef, rainWindRef, snowBodyRefs, petalBodyRefs)
    }
  }, [active, motionRef, rainWindRef, snowBodyRefs, petalBodyRefs, snowLeftPct, petalLeftPct])
}
