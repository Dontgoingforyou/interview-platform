import { buildDirectionObservationsLines } from '../../utils/directions/directionsObservationsText'
import type { DirectionObservationsResponse } from '../../types/direction'

interface DirectionObservationsBlockProps {
  data: DirectionObservationsResponse | undefined
  isError: boolean
}

/** Блок текстовых наблюдений по направлениям. */
function DirectionObservationsBlock({ data, isError }: DirectionObservationsBlockProps) {
  if (isError) {
    return <p className="managers-observations-empty">Ошибка загрузки наблюдений.</p>
  }
  if (!data) {
    return <p className="managers-observations-empty">Загрузка наблюдений…</p>
  }
  if (data.totalDirections === 0) {
    return <p className="managers-observations-empty">Нет данных для формирования наблюдений.</p>
  }

  const lines = buildDirectionObservationsLines(data)
  return (
    <div className="managers-observations-list">
      {lines.map((line, index) => (
        <p key={index} className="managers-observation">
          {line}
        </p>
      ))}
    </div>
  )
}

export default DirectionObservationsBlock
