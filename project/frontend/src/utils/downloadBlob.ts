import type { AxiosResponse } from 'axios'

/**
 * Скачивание файла из ответа axios с responseType: 'blob'.
 * Имя берётся из Content-Disposition, иначе fallbackFilename.
 */
export function downloadBlobResponse(response: AxiosResponse<Blob>, fallbackFilename: string): void {
  const blob = response.data
  const cd = response.headers['content-disposition'] as string | undefined
  let filename = fallbackFilename
  if (cd) {
    const match = /filename="?([^";\n]+)"?/i.exec(cd)
    if (match?.[1]) {
      filename = match[1].trim()
    }
  }
  const url = URL.createObjectURL(blob)
  try {
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}
