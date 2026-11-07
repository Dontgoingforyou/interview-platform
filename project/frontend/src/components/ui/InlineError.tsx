interface InlineErrorProps {
  message: string
}

function InlineError({ message }: InlineErrorProps) {
  return (
    <p className="form-error" role="alert">
      {message}
    </p>
  )
}

export default InlineError
