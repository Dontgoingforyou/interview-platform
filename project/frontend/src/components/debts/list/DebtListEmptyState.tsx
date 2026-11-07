/** Пустой список долгов. */
function DebtListEmptyState() {
  return (
    <p className="empty-state-msg" role="status">
      Нет записей о долгах по текущим фильтрам.
    </p>
  )
}

export default DebtListEmptyState
