import type { FormHTMLAttributes, HTMLAttributes, ReactNode } from 'react'

function buildClass(interviewsScoped: boolean, extra?: string): string {
  return ['filter-form', interviewsScoped ? 'interviews-filters' : '', 'list-page-filters', extra ?? '']
    .filter(Boolean)
    .join(' ')
}

type FormProps = Omit<FormHTMLAttributes<HTMLFormElement>, 'className' | 'children'>
type DivProps = Omit<HTMLAttributes<HTMLDivElement>, 'className' | 'children'>

type ListPageFilterFormProps = {
  children: ReactNode
  /** Дополнительные классы (например filter-form-wide, debt-by-month-filters). */
  className?: string
  /**
   * Если false — только `filter-form` + `list-page-filters` (список компаний без scope интервью).
   * @default true
   */
  interviewsScoped?: boolean
} & (
  | ({ as?: 'form' } & FormProps)
  | ({ as: 'div' } & DivProps)
)

/**
 * Оболочка фильтров списков: единые классы из list-pages.css.
 * По умолчанию — form; для блоков без submit (только кнопки «Применить» с onClick) — as="div".
 */
function ListPageFilterForm(props: ListPageFilterFormProps) {
  const {
    children,
    className = '',
    interviewsScoped = true,
    as = 'form',
    ...rest
  } = props as ListPageFilterFormProps & { as?: 'form' | 'div' }
  const cls = buildClass(interviewsScoped, className)
  if (as === 'div') {
    return (
      <div className={cls} {...(rest as DivProps)}>
        {children}
      </div>
    )
  }
  return (
    <form className={cls} {...(rest as FormProps)}>
      {children}
    </form>
  )
}

export default ListPageFilterForm
