import { buildManagersObservationLines } from '../../../utils/managers/managersObservationsText'
import type { ManagersObservations } from '../../../types/managerDashboard'

interface ManagersObservationsSectionProps {
  data: ManagersObservations | undefined
}

function ManagersObservationsSection({ data }: ManagersObservationsSectionProps) {
  if (!data) {
    return null
  }

  if (data.totalManagers === 0) {
    return <p className="managers-observations-empty">Нет данных для формирования наблюдений.</p>
  }

  const lines = buildManagersObservationLines(data)

  return (
    <div className="managers-observations-list">
      {lines.map((text, idx) => (
        <div key={idx} className="managers-observation">
          {text}
        </div>
      ))}
    </div>
  )
}

export default ManagersObservationsSection
