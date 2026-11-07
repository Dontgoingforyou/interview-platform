import { describe, expect, it } from 'vitest'

import {
  internPortalCeleryFailureMessage,
  internPortalUploadErrorMessage,
} from '../../../utils/internsPortal/uploadErrors'

describe('uploadErrors edges', () => {
  it('409 без текста сервера → дефолт', () => {
    expect(
      internPortalUploadErrorMessage({ response: { status: 409, data: {} } }),
    ).toContain('уже выполняется')
  })

  it('произвольный статус с detail', () => {
    expect(
      internPortalUploadErrorMessage({
        response: { status: 400, data: { detail: 'Файл слишком большой' } },
      }),
    ).toBe('Файл слишком большой')
  })

  it('без ответа → сеть/размер', () => {
    expect(internPortalUploadErrorMessage({})).toContain('Не удалось отправить')
  })

  it('celery: пустой и короткий статус', () => {
    expect(internPortalCeleryFailureMessage(undefined)).toContain('облачное')
    expect(internPortalCeleryFailureMessage('  ')).toContain('облачное')
    expect(internPortalCeleryFailureMessage('fail')).toBe('fail')
  })
})
