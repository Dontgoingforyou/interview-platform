interface LoadingLineProps {
  /** Текст вроде «Загрузка метрик…» */
  message?: string
}

function LoadingLine({ message = 'Загрузка…' }: LoadingLineProps) {
  return <p className="page-loading-hint">{message}</p>
}

export default LoadingLine
