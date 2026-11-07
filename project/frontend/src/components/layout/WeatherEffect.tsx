import { useRef } from 'react'

import {
  isWeatherInteractiveTheme,
  useDocumentTheme,
  useReducedMotionPreference,
  useWeatherInteractiveMotion,
} from '../../hooks/useWeatherInteractiveMotion'

/**
 * Детерминированный линейный конгруэнтный генератор (LCG).
 * Фиксированный seed → одинаковые значения при каждом рендере без useState/useEffect.
 */
function makeLcg(seed: number): () => number {
  let s = seed >>> 0
  return () => {
    s = Math.imul(s, 1664525) + 1013904223
    return (s >>> 0) / 4294967295
  }
}

interface ParticleStyle {
  left: string
  leftPct: number
  animationDuration: string
  animationDelay: string
}

function generateParticles(
  count: number,
  seed: number,
  durationMin: number,
  durationMax: number,
  delayMax: number,
): ParticleStyle[] {
  const rand = makeLcg(seed)
  return Array.from({ length: count }, () => {
    const leftPct = rand() * 97 + 1
    return {
      left: `${leftPct.toFixed(1)}%`,
      leftPct,
      animationDuration: `${(rand() * (durationMax - durationMin) + durationMin).toFixed(2)}s`,
      animationDelay: `${(rand() * delayMax).toFixed(2)}s`,
    }
  })
}

/* Вычисляется один раз при загрузке модуля — не нужны хуки */
const SNOWFLAKE_STYLES = generateParticles(56, 11, 10, 17, 3.5)
const RAINDROP_STYLES = generateParticles(56, 22, 0.35, 0.58, 0.72)
const PETAL_STYLES = generateParticles(30, 33, 17, 27, 5)

const SNOW_LEFT_PCT = SNOWFLAKE_STYLES.map((s) => s.leftPct)
const PETAL_LEFT_PCT = PETAL_STYLES.map((s) => s.leftPct)

export default function WeatherEffect() {
  const theme = useDocumentTheme()
  const reducedMotion = useReducedMotionPreference()
  const motionRef = useRef<HTMLDivElement>(null)
  const rainWindRef = useRef<HTMLDivElement>(null)
  const snowBodyRefs = useRef<(HTMLSpanElement | null)[]>([])
  const petalBodyRefs = useRef<(HTMLSpanElement | null)[]>([])

  const interactiveActive = isWeatherInteractiveTheme(theme) && !reducedMotion

  useWeatherInteractiveMotion(
    interactiveActive,
    motionRef,
    rainWindRef,
    snowBodyRefs,
    petalBodyRefs,
    SNOW_LEFT_PCT,
    PETAL_LEFT_PCT,
  )

  const trackTiming = (s: ParticleStyle) => ({
    animationDuration: s.animationDuration,
    animationDelay: s.animationDelay,
  })

  return (
    <div className="weather-effect" aria-hidden="true">
      <div ref={motionRef} className="weather-effect__motion">
        {SNOWFLAKE_STYLES.map((style, i) => (
          <span key={`s-${i}`} className="snowflake" style={{ left: style.left }}>
            <span className="snowflake__track" style={trackTiming(style)}>
              <span
                ref={(el) => {
                  snowBodyRefs.current[i] = el
                }}
                className="snowflake__body"
              />
            </span>
          </span>
        ))}
        <div ref={rainWindRef} className="weather-effect__rain">
          {RAINDROP_STYLES.map((style, i) => (
            <span key={`r-${i}`} className="raindrop" style={{ left: style.left }}>
              <span className="raindrop__track" style={trackTiming(style)}>
                <span className="raindrop__body" />
              </span>
            </span>
          ))}
        </div>
        {PETAL_STYLES.map((style, i) => (
          <span key={`p-${i}`} className="petal" style={{ left: style.left }}>
            <span className="petal__track" style={trackTiming(style)}>
              <span
                ref={(el) => {
                  petalBodyRefs.current[i] = el
                }}
                className="petal__body"
              />
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
