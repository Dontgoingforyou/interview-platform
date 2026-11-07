interface InterviewListEmptyStateProps {
  filtersActive: boolean
  onResetFilters: () => void
}

function InterviewListEmptyState({ filtersActive, onResetFilters }: InterviewListEmptyStateProps) {
  return (
    <div className="interviews-empty-state" role="status">
      <p className="interviews-empty-state__title">Записей не найдено</p>
      <p className="interviews-empty-state__text">
        {filtersActive
          ? 'Попробуйте изменить фильтры или сбросить параметры поиска.'
          : 'Пока нет собеседований, попадающих под текущие условия.'}
      </p>
      {filtersActive ? (
        <button type="button" className="btn-secondary" onClick={onResetFilters}>
          Сбросить фильтры
        </button>
      ) : null}
    </div>
  )
}

export default InterviewListEmptyState
