/* eslint-disable react-hooks/set-state-in-effect --
   Модалка: монтирование и fade привязаны к isOpen родителя; отложенные setState в rAF/таймере. */
import { useCallback, useEffect, useRef, useState } from 'react'

const FADE_MS = 280

type Options = {
  onExitComplete: () => void
}

/**
 * Плавное появление/исчезновение модалки (оверлей + панель по классам open).
 */
export function useModalEnterExit(isOpen: boolean, { onExitComplete }: Options) {
  const [mounted, setMounted] = useState(false)
  const [openClass, setOpenClass] = useState(false)
  const completeRef = useRef(onExitComplete)
  const exitingRef = useRef(false)

  useEffect(() => {
    completeRef.current = onExitComplete
  }, [onExitComplete])
  /** В браузере window.setTimeout возвращает number; не NodeJS.Timeout. */
  const timerRef = useRef<number | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const beginExit = useCallback(() => {
    if (exitingRef.current) {
      return
    }
    exitingRef.current = true
    setOpenClass(false)
    clearTimer()
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null
      exitingRef.current = false
      setMounted(false)
      completeRef.current()
    }, FADE_MS)
  }, [clearTimer])

  useEffect(() => {
    if (!isOpen) {
      return
    }
    exitingRef.current = false
    clearTimer()
    setMounted(true)
    setOpenClass(false)
    const id = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => setOpenClass(true))
    })
    return () => window.cancelAnimationFrame(id)
  }, [isOpen, clearTimer])

  /** Родитель сбросил isOpen, а модалка ещё смонтирована — добиваем анимацию закрытия. */
  useEffect(() => {
    if (isOpen || !mounted) {
      return
    }
    if (exitingRef.current) {
      return
    }
    beginExit()
  }, [isOpen, mounted, beginExit])

  const requestClose = useCallback(() => {
    beginExit()
  }, [beginExit])

  useEffect(() => () => clearTimer(), [clearTimer])

  return {
    shouldMount: mounted,
    overlayOpenClass: openClass ? 'interviews-modal-fade--open' : '',
    requestClose,
  }
}
