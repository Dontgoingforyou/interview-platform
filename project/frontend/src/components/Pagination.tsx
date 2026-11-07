import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  /** Показать поле ввода «перейти на страницу». */
  showPageInput?: boolean
}

/** Пагинация: предыдущая/следующая, номера страниц, опционально ввод номера. */
function Pagination({ currentPage, totalPages, onPageChange, showPageInput }: PaginationProps) {
  const [jumpValue, setJumpValue] = useState(String(currentPage))

  useEffect(() => {
    setJumpValue(String(currentPage))
  }, [currentPage])

  if (totalPages <= 1) {
    return null
  }

  const hasPrev = currentPage > 1
  const hasNext = currentPage < totalPages

  function handleJumpSubmit(e: FormEvent) {
    e.preventDefault()
    const n = parseInt(jumpValue, 10)
    if (Number.isNaN(n) || n < 1 || n > totalPages) {
      setJumpValue(String(currentPage))
      return
    }
    onPageChange(n)
  }

  return (
    <nav className="pagination-nav" aria-label="Страницы">
      <ul className="pagination">
        {showPageInput ? (
          <li className="page-item">
            <form className="pagination-form" onSubmit={handleJumpSubmit}>
              <span className="pagination-form-label">Стр.</span>
              <input
                type="number"
                name="page"
                min={1}
                max={totalPages}
                className="pagination-form-input"
                value={jumpValue}
                onChange={(e) => setJumpValue(e.target.value)}
                aria-label="Номер страницы"
              />
              <button type="submit" className="pagination-jump-btn">
                Перейти
              </button>
            </form>
          </li>
        ) : null}

        {hasPrev ? (
          <>
            <li className="page-item">
              <button type="button" className="page-link" onClick={() => onPageChange(1)}>
                « Первая
              </button>
            </li>
            <li className="page-item">
              <button type="button" className="page-link" onClick={() => onPageChange(currentPage - 1)}>
                Назад
              </button>
            </li>
          </>
        ) : null}

        <li className="page-item page-item--info">
          <span className="page-link page-link--static">
            {currentPage} из {totalPages}
          </span>
        </li>

        {hasNext ? (
          <>
            <li className="page-item">
              <button type="button" className="page-link" onClick={() => onPageChange(currentPage + 1)}>
                Вперёд
              </button>
            </li>
            <li className="page-item">
              <button type="button" className="page-link" onClick={() => onPageChange(totalPages)}>
                Последняя »
              </button>
            </li>
          </>
        ) : null}
      </ul>
    </nav>
  )
}

export default Pagination
