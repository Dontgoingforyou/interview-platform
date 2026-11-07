import { describe, expect, it } from 'vitest'

import { toast } from '../../utils/toast'

describe('toast', () => {
  it('re-export из sonner доступен', () => {
    expect(typeof toast.success).toBe('function')
    expect(typeof toast.error).toBe('function')
  })
})
