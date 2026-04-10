const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

type PingResponse = {
  message: string
}

export async function getPingMessage(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/ping`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const data = (await response.json()) as PingResponse
  return data.message
}
