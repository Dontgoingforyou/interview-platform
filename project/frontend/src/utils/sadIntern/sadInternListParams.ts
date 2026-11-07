import type { OrderDir } from '../../types/common'
import type { SadInternListFilters } from '../../types/sadIntern'

export const SAD_INTERN_DEFAULT_ORDER_BY = 'days_waiting'
export const SAD_INTERN_DEFAULT_ORDER_DIR: OrderDir = 'desc'

/** Ключи пагинации/сортировки, не считающиеся «смысловыми» фильтрами. */
export const SAD_INTERN_LIST_META_KEYS = new Set(['order_by', 'order_dir', 'on_project_page'])

export function parseSadInternGroupPages(sp: URLSearchParams): Record<string, number> {
  const out: Record<string, number> = {}
  for (const [k, v] of sp.entries()) {
    if (!k.startsWith('page_')) {
      continue
    }
    const suffix = k.slice(5)
    const n = parseInt(v, 10)
    if (!Number.isNaN(n) && n >= 1) {
      out[suffix] = n
    }
  }
  return out
}

export function parseSadInternListFromSearchParams(sp: URLSearchParams): SadInternListFilters {
  const q = sp.get('q')?.trim() || undefined
  const status = sp.get('status')?.trim() || undefined
  const dirRaw = sp.get('direction')
  let direction: number | null | undefined
  if (dirRaw) {
    const d = parseInt(dirRaw, 10)
    direction = Number.isNaN(d) ? undefined : d
  } else {
    direction = undefined
  }

  const ob = sp.get('order_by')?.trim() || SAD_INTERN_DEFAULT_ORDER_BY
  const od = (sp.get('order_dir') === 'asc' ? 'asc' : 'desc') as OrderDir

  const opp = sp.get('on_project_page')
  let on_project_page = 1
  if (opp) {
    const p = parseInt(opp, 10)
    if (!Number.isNaN(p) && p >= 1) {
      on_project_page = p
    }
  }

  return {
    q,
    status,
    direction: direction === undefined ? undefined : direction,
    order_by: ob,
    order_dir: od,
    on_project_page,
  }
}

export function buildSadInternGroupedParams(
  filters: SadInternListFilters,
  directionsOffset: number,
  groupPages: Record<string, number>,
): Record<string, string | number> {
  const p: Record<string, string | number> = {
    order_by: filters.order_by,
    order_dir: filters.order_dir,
    directions_offset: directionsOffset,
  }
  if (filters.q) {
    p.q = filters.q
  }
  if (filters.status) {
    p.status = filters.status
  }
  if (filters.direction != null && filters.direction !== undefined) {
    p.direction = filters.direction
  }
  for (const [key, page] of Object.entries(groupPages)) {
    if (page >= 1) {
      // pagination_key с API уже в виде page_<id|none>; из URL parseSadInternGroupPages — ключ без префикса
      const paramKey = key.startsWith('page_') ? key : `page_${key}`
      p[paramKey] = page
    }
  }
  return p
}

export function buildSadInternOnProjectParams(filters: SadInternListFilters): Record<string, string | number> {
  const p: Record<string, string | number> = {
    on_project_page: filters.on_project_page,
  }
  if (filters.q) {
    p.q = filters.q
  }
  if (filters.status) {
    p.status = filters.status
  }
  if (filters.direction != null && filters.direction !== undefined) {
    p.direction = filters.direction
  }
  return p
}

/** Стабильная подпись семантических фильтров для queryKey (без directions_offset и groupPages). */
export function sadInternGroupedFilterKey(filters: SadInternListFilters): string {
  return JSON.stringify({
    q: filters.q ?? '',
    status: filters.status ?? '',
    direction: filters.direction ?? '',
    order_by: filters.order_by,
    order_dir: filters.order_dir,
  })
}
