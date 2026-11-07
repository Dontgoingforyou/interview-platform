import { useEffect, useId, useState } from 'react'

import {
  WHATS_NEW_ENTRIES,
  changelogSeenStorageKey,
  hasUnseenWhatsNew,
  type WhatsNewEntry,
} from '../../constants/changelog'
import { useModalEnterExit } from '../../hooks/useModalEnterExit'
import { useAuthStore } from '../../store/authStore'
import { isPureStudentPortalUser } from '../../utils/authRoles'
import ChangelogList from './ChangelogList'

function readSeenVersion(username: string): string | null {
  if (!username) {
    return null
  }
  try {
    return localStorage.getItem(changelogSeenStorageKey(username))
  } catch {
    return null
  }
}

function rememberSeenVersion(username: string, version: string) {
  if (!username) {
    return
  }
  try {
    localStorage.setItem(changelogSeenStorageKey(username), version)
  } catch {
    // приватный режим без хранилища — кружок останется до перезагрузки
  }
}

type ChangelogButtonProps = {
  entries?: readonly WhatsNewEntry[]
}

function ChangelogButton({ entries = WHATS_NEW_ENTRIES }: ChangelogButtonProps) {
  const authUser = useAuthStore((s) => s.user)
  const username = authUser?.username ?? ''
  const latestVersion = entries[0]?.version ?? null
  const [open, setOpen] = useState(false)
  const [seenFor, setSeenFor] = useState(() => ({
    username,
    version: readSeenVersion(username),
  }))
  const titleId = useId()
  const modal = useModalEnterExit(open, { onExitComplete: () => setOpen(false) })

  if (seenFor.username !== username) {
    setSeenFor({ username, version: readSeenVersion(username) })
  }

  const unseen = hasUnseenWhatsNew(seenFor.version, latestVersion)
  const label = unseen ? 'Что нового, есть непрочитанное обновление' : 'Что нового'

  useEffect(() => {
    if (!modal.shouldMount) {
      return
    }
    // scrollbar-gutter: stable уже держит место полосы. data-scroll-lock его снимает
    // и страница прыгает вправо-влево, как у других модалок. Здесь только прячем прокрутку.
    const html = document.documentElement
    const body = document.body
    const prevHtmlOverflow = html.style.overflow
    const prevBodyOverflow = body.style.overflow
    html.style.overflow = 'hidden'
    body.style.overflow = 'hidden'
    return () => {
      html.style.overflow = prevHtmlOverflow
      body.style.overflow = prevBodyOverflow
    }
  }, [modal.shouldMount])

  useEffect(() => {
    if (!modal.shouldMount) {
      return
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        modal.requestClose()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [modal])

  if (isPureStudentPortalUser(authUser)) {
    return null
  }

  function openChangelog() {
    setOpen(true)
    if (latestVersion != null && username && seenFor.version !== latestVersion) {
      rememberSeenVersion(username, latestVersion)
      setSeenFor({ username, version: latestVersion })
    }
  }

  return (
    <>
      <span className="changelog-btn-wrap">
        <button
          type="button"
          className={open ? 'changelog-btn is-active' : 'changelog-btn'}
          aria-label={label}
          title="Что нового"
          onClick={openChangelog}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M3 12a9 9 0 1 0 3-6.7" />
            <path d="M3 4v5h5" />
            <path d="M12 7v5l3 2" />
          </svg>
        </button>
        {unseen ? <span className="changelog-dot" aria-hidden /> : null}
      </span>
      {modal.shouldMount ? (
        <div
          className={`changelog-overlay ${modal.overlayOpenClass}`}
          role="presentation"
          onClick={() => modal.requestClose()}
        >
          <div
            className="changelog-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id={titleId} className="changelog-dialog-title">Что нового</h2>
            <div className="changelog-dialog-body">
              <ChangelogList entries={entries} />
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}

export default ChangelogButton
