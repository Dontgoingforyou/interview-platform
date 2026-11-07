import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { createDirection } from '../../api/directionsApi'
import { useAuthStore } from '../../store/authStore'
import { isAdminUser } from '../../utils/authRoles'
import { toast } from '../../utils/toast'

/**
 * Создание направления (только администратор).
 */
function DirectionFormPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = isAdminUser(user)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createDirection({ name: name.trim() }),
    onSuccess: () => {
      toast.success('Направление добавлено')
      void queryClient.invalidateQueries({ queryKey: ['directions', 'metrics'] })
      void queryClient.invalidateQueries({ queryKey: ['directions', 'observations'] })
      void queryClient.invalidateQueries({ queryKey: ['directions-options'] })
      navigate('/directions', { replace: true })
    },
    onError: () => {
      toast.error('Не удалось сохранить направление')
    },
  })

  if (!isAdmin) {
    return <Navigate to="/directions" replace />
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFieldError(null)
    const trimmed = name.trim()
    if (!trimmed) {
      setFieldError('Укажите название')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="page direction-form-page">
      <h1 className="page-title">Новое направление</h1>
      <p className="direction-form-lead muted">
        Добавление направления в справочник (используется в собеседованиях и отчётах).
      </p>

      <div className="interview-form-back-row">
        <Link to="/directions" className="btn-secondary">
          ← К метрикам по направлениям
        </Link>
      </div>

      <form className="interview-form direction-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="direction-name">
          Название
          <input
            id="direction-name"
            type="text"
            name="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={255}
            autoComplete="off"
            placeholder="Например, Python"
            disabled={mutation.isPending}
            aria-invalid={Boolean(fieldError)}
            aria-describedby={fieldError ? 'direction-name-error' : undefined}
          />
          {fieldError ? (
            <span id="direction-name-error" className="form-error" role="alert">
              {fieldError}
            </span>
          ) : null}
        </label>

        <div className="direction-form-actions">
          <button type="submit" className="btn-success" disabled={mutation.isPending}>
            {mutation.isPending ? 'Сохранение…' : 'Сохранить'}
          </button>
          <Link to="/directions" className="btn-secondary">
            Отмена
          </Link>
        </div>
      </form>
    </div>
  )
}

export default DirectionFormPage
