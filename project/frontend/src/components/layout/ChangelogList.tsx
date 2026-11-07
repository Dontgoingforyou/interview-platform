import { useState } from 'react'

import {
  WHATS_NEW_EMPTY_TEXT,
  WHATS_NEW_ENTRIES,
  formatWhatsNewDate,
  whatsNewPage,
  type WhatsNewEntry,
} from '../../constants/changelog'

type ChangelogListProps = {
  entries?: readonly WhatsNewEntry[]
}

function ChangelogList({ entries = WHATS_NEW_ENTRIES }: ChangelogListProps) {
  const [loadedPages, setLoadedPages] = useState(1)
  const visible = Array.from({ length: loadedPages }, (_, pageIndex) => whatsNewPage(entries, pageIndex)).flat()
  const hasMore = whatsNewPage(entries, loadedPages).length > 0

  if (entries.length === 0) {
    return <p className="changelog-empty">{WHATS_NEW_EMPTY_TEXT}</p>
  }

  return (
    <div className="changelog-list-wrap">
      <ol className="changelog-list">
        {visible.map((entry, index) => (
          <li key={entry.version} className={index === 0 ? 'changelog-entry is-latest' : 'changelog-entry'}>
            <p className="changelog-version">{entry.version}</p>
            <time className="changelog-date" dateTime={entry.date}>
              {formatWhatsNewDate(entry.date)}
            </time>
            <p className="changelog-text">{entry.text}</p>
          </li>
        ))}
      </ol>
      {hasMore ? (
        <button type="button" className="changelog-more" onClick={() => setLoadedPages((pages) => pages + 1)}>
          Показать предыдущие
        </button>
      ) : null}
    </div>
  )
}

export default ChangelogList
