<template>
  <div class="settings-container">
    <nav class="navbar">
      <div class="nav-brand" @click="goHome" style="cursor: pointer">MIROFISH</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">Home</router-link>
      </div>
    </nav>

    <div class="settings-content">
      <div class="settings-header">
        <h1 class="settings-title">Settings</h1>
        <p class="settings-desc">Configure your AI provider. Your API key is stored locally in your browser and never sent to our servers — it goes directly to the provider you choose.</p>
      </div>

      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">&#9670;</span> LLM Provider
        </div>

        <div class="field-group">
          <label class="field-label">Provider</label>
          <select v-model="settings.provider" class="field-select" @change="onProviderChange">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic (via OpenAI-compatible proxy)</option>
            <option value="custom">Custom (OpenAI-compatible)</option>
          </select>
        </div>

        <div class="field-group">
          <label class="field-label">API Key</label>
          <div class="field-input-wrapper">
            <input
              :type="showKey ? 'text' : 'password'"
              v-model="settings.apiKey"
              class="field-input"
              placeholder="sk-..."
            />
            <button class="toggle-btn" @click="showKey = !showKey">
              {{ showKey ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">Base URL</label>
          <input
            type="text"
            v-model="settings.baseUrl"
            class="field-input"
            placeholder="https://api.openai.com/v1"
          />
        </div>

        <div class="field-group">
          <label class="field-label">Model</label>
          <input
            type="text"
            v-model="settings.model"
            class="field-input"
            :placeholder="modelPlaceholder"
          />
        </div>

        <div class="actions-row">
          <button class="btn-save" @click="saveSettings">Save Settings</button>
          <button class="btn-test" @click="testConnection" :disabled="testing">
            {{ testing ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>

        <div v-if="message" :class="['status-message', messageType]">
          {{ message }}
        </div>
      </div>

      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">&#9670;</span> About
        </div>
        <p class="about-text">
          MiroFish is a multi-agent swarm simulation engine. Upload any document and watch hundreds of AI agents debate, react, and evolve opinions — giving you a preview of how real people might respond.
        </p>
        <p class="about-text" style="margin-top: 10px; color: #999;">
          Your API key never leaves your browser. All LLM calls go directly from the backend to your chosen provider.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import service from '../api/index'

const router = useRouter()
const showKey = ref(false)
const testing = ref(false)
const message = ref('')
const messageType = ref('success')

const STORAGE_KEY = 'mirofish_settings'

const settings = reactive({
  provider: 'openai',
  apiKey: '',
  baseUrl: 'https://api.openai.com/v1',
  model: 'gpt-4o-mini',
})

const modelPlaceholder = computed(() => {
  if (settings.provider === 'openai') return 'gpt-4o-mini'
  if (settings.provider === 'anthropic') return 'claude-sonnet-4-20250514'
  return 'model-name'
})

const providerDefaults = {
  openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  anthropic: { baseUrl: 'https://api.anthropic.com/v1', model: 'claude-sonnet-4-20250514' },
  custom: { baseUrl: '', model: '' },
}

function onProviderChange() {
  const defaults = providerDefaults[settings.provider]
  settings.baseUrl = defaults.baseUrl
  settings.model = defaults.model
}

function loadSettings() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      Object.assign(settings, parsed)
    }
  } catch (e) {
    console.warn('Failed to load settings:', e)
  }
}

function saveSettings() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...settings }))
    message.value = 'Settings saved successfully.'
    messageType.value = 'success'
  } catch (e) {
    message.value = 'Failed to save settings.'
    messageType.value = 'error'
  }
}

async function testConnection() {
  if (!settings.apiKey) {
    message.value = 'Please enter an API key first.'
    messageType.value = 'error'
    return
  }

  testing.value = true
  message.value = ''

  try {
    const res = await service.post('/api/settings/test', {
      api_key: settings.apiKey,
      base_url: settings.baseUrl,
      model: settings.model,
    })
    message.value = res.message || 'Connection successful!'
    messageType.value = 'success'
  } catch (e) {
    message.value = e.response?.data?.error || e.message || 'Connection failed.'
    messageType.value = 'error'
  } finally {
    testing.value = false
  }
}

function goHome() {
  router.push('/')
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: #fff;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  color: #000;
}

.navbar {
  height: 60px;
  background: #000;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  color: #fff;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 500;
}

.nav-link:hover {
  opacity: 0.8;
}

.settings-content {
  max-width: 640px;
  margin: 0 auto;
  padding: 60px 20px;
}

.settings-header {
  margin-bottom: 40px;
}

.settings-title {
  font-size: 2.5rem;
  font-weight: 500;
  margin: 0 0 12px 0;
  letter-spacing: -1px;
}

.settings-desc {
  color: #666;
  line-height: 1.6;
  font-size: 0.95rem;
}

.settings-card {
  border: 1px solid #e5e5e5;
  padding: 30px;
  margin-bottom: 24px;
}

.card-header {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  color: #FF4500;
  font-size: 0.9rem;
}

.field-group {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-input,
.field-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  background: #fafafa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}

.field-input:focus,
.field-select:focus {
  border-color: #000;
}

.field-select {
  appearance: auto;
}

.field-input-wrapper {
  display: flex;
  gap: 8px;
}

.field-input-wrapper .field-input {
  flex: 1;
}

.toggle-btn {
  padding: 12px 16px;
  border: 1px solid #ddd;
  background: #fafafa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}

.toggle-btn:hover {
  background: #f0f0f0;
}

.actions-row {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-save,
.btn-test {
  padding: 14px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  letter-spacing: 0.5px;
  border: none;
}

.btn-save {
  background: #000;
  color: #fff;
  flex: 1;
}

.btn-save:hover {
  background: #FF4500;
}

.btn-test {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.btn-test:hover {
  background: #f0f0f0;
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-message {
  margin-top: 16px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.status-message.success {
  background: #f0fff0;
  border: 1px solid #4caf50;
  color: #2e7d32;
}

.status-message.error {
  background: #fff0f0;
  border: 1px solid #f44336;
  color: #c62828;
}

.about-text {
  color: #666;
  line-height: 1.6;
  font-size: 0.9rem;
}
</style>
