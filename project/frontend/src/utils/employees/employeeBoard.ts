/**
 * Подпись направления по словарю id → название (как на доске менеджера).
 */
export function employeeBoardDirectionLabel(
  directionsDict: Record<string, string>,
  directionId: number | null,
): string {
  if (directionId == null) {
    return '—'
  }
  return directionsDict[String(directionId)] ?? '—'
}
