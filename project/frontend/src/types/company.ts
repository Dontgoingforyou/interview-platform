import type { Paginated } from './common'

/** Элемент списка / детали компании (ответ DRF). */
export interface CompanyListItem {
  id: number
  name: string
  is_bigtech: boolean
  aliases: string
  aliases_list: string[]
  interviews_count: number
}

/** Сводка для шапки списка. */
export interface CompanyStats {
  total_count: number
  bigtech_count: number
  with_interviews_count: number
  without_interviews_count: number
}

/** Параметры списка в URL и для API. */
export interface CompanyListFilters {
  q: string
  /** Пусто — все; '1' — только бигтех; '0' — не бигтех. */
  bigtech: '' | '0' | '1'
  sort: 'interviews' | '-interviews' | 'name' | '-name'
  page: number
}

export type CompanyWritePayload = {
  name: string
  is_bigtech: boolean
  aliases: string
}

export interface CompanyMergeResponse {
  primary_id: number
  primary_name: string
  removed_ids: number[]
  removed_names: string[]
  interviews_moved: number
}

export type PaginatedCompanies = Paginated<CompanyListItem>
