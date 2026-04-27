const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

type PingResponse = {
  message: string
}

type FrontendToControllerRequest = {
  user_input: string
  interaction_info?: Record<string, any>
}

type ControllerToFrontendResponse = {
  reply_text: string
  structured_task_output?: Record<string, any> | null
}

export async function getPingMessage(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/ping`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const data = (await response.json()) as PingResponse
  return data.message
}

export async function sendUserRequest(userInput: string): Promise<ControllerToFrontendResponse> {
  const payload: FrontendToControllerRequest = {
    user_input: userInput,
    interaction_info: {}
  }

  const response = await fetch(`${API_BASE_URL}/api/raw-request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return (await response.json()) as ControllerToFrontendResponse
}
