const STORAGE_KEY = 'llmConfig'

const DEFAULT_CONFIG = {
  model: 'ollama/qwen2.5:7b',
  apiKey: null,
}

export function getLlmConfig() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) return DEFAULT_CONFIG
  try {
    return { ...DEFAULT_CONFIG, ...JSON.parse(stored) }
  } catch {
    return DEFAULT_CONFIG
  }
}

export function setLlmConfig({ model, apiKey }) {
  const config = { model, apiKey }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  return config
}
