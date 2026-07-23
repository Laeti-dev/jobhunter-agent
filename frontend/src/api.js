import { getLlmConfig } from './llmConfig'

const BASE_URL = 'http://localhost:8000'

export function apiFetch(path, options = {}) {
  const { model, apiKey } = getLlmConfig()

  const headers = {
    ...options.headers,
    'X-Llm-Model': model,
  }
  if (apiKey) {
    headers['X-Llm-Api-Key'] = apiKey
  }

  return fetch(`${BASE_URL}${path}`, { ...options, headers })
}
