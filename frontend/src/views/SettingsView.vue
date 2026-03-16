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
          <span class="card-icon">&#9670;</span> AI Provider
        </div>

        <div class="field-group">
          <label class="field-label">Provider</label>
          <div class="provider-grid">
            <div
              v-for="p in providers"
              :key="p.id"
              :class="['provider-card', { active: settings.provider === p.id }]"
              @click="selectProvider(p.id)"
            >
              <div class="provider-name">{{ p.name }}</div>
              <div class="provider-desc">{{ p.description }}</div>
            </div>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">API Key</label>
          <div class="field-input-wrapper">
            <input
              :type="showKey ? 'text' : 'password'"
              v-model="settings.apiKey"
              class="field-input"
              :placeholder="keyPlaceholder"
            />
            <button class="toggle-btn" @click="showKey = !showKey">
              {{ showKey ? 'Hide' : 'Show' }}
            </button>
          </div>
          <div class="field-hint" v-if="selectedProvider">
            Get your key at <a :href="selectedProvider.keyUrl" target="_blank" class="field-link">{{ selectedProvider.keyUrlLabel }}</a>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">Model</label>
          <div class="model-grid">
            <div
              v-for="m in availableModels"
              :key="m.id"
              :class="['model-card', { active: settings.model === m.id }]"
              @click="selectModel(m)"
            >
              <div class="model-top">
                <span class="model-name">{{ m.name }}</span>
                <span :class="['cost-badge', m.costClass]">{{ m.cost }}</span>
              </div>
              <div class="model-desc">{{ m.desc }}</div>
            </div>
          </div>
        </div>

        <div v-if="settings.provider === 'custom'" class="field-group">
          <label class="field-label">Base URL</label>
          <input
            type="text"
            v-model="settings.baseUrl"
            class="field-input"
            placeholder="https://your-api.example.com/v1"
          />
        </div>

        <div v-if="settings.provider === 'custom'" class="field-group">
          <label class="field-label">Model ID</label>
          <input
            type="text"
            v-model="settings.model"
            class="field-input"
            placeholder="model-name"
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

const providers = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4o, GPT-4o mini, o3-mini',
    keyUrl: 'https://platform.openai.com/api-keys',
    keyUrlLabel: 'platform.openai.com',
    keyPlaceholder: 'sk-...',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude Haiku, Sonnet, Opus',
    keyUrl: 'https://console.anthropic.com/settings/keys',
    keyUrlLabel: 'console.anthropic.com',
    keyPlaceholder: 'sk-ant-...',
  },
  {
    id: 'google',
    name: 'Google AI',
    description: 'Gemini Flash, Pro',
    keyUrl: 'https://aistudio.google.com/apikey',
    keyUrlLabel: 'aistudio.google.com',
    keyPlaceholder: 'AIza...',
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'All models, one key',
    keyUrl: 'https://openrouter.ai/keys',
    keyUrlLabel: 'openrouter.ai',
    keyPlaceholder: 'sk-or-...',
  },
  {
    id: 'custom',
    name: 'Custom',
    description: 'Any OpenAI-compatible API',
    keyUrl: '',
    keyUrlLabel: '',
    keyPlaceholder: 'your-api-key',
  },
]

const modelCatalog = {
  openai: [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', cost: '$', costClass: 'cheap', desc: 'Fast and affordable. Great for most simulations.' },
    { id: 'gpt-4o', name: 'GPT-4o', cost: '$$', costClass: 'mid', desc: 'Smarter, better reasoning. For complex scenarios.' },
    { id: 'o3-mini', name: 'o3-mini', cost: '$$', costClass: 'mid', desc: 'Advanced reasoning model. Best for analysis.' },
  ],
  anthropic: [
    { id: 'claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', cost: '$', costClass: 'cheap', desc: 'Fastest and cheapest. Perfect for large agent swarms.' },
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', cost: '$$', costClass: 'mid', desc: 'Balanced speed and intelligence.' },
    { id: 'claude-opus-4-20250918', name: 'Claude Opus 4', cost: '$$$', costClass: 'premium', desc: 'Most capable. Best for deep analysis and reports.' },
  ],
  google: [
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', cost: '$', costClass: 'cheap', desc: 'Extremely fast and cheap. Great for large simulations.' },
    { id: 'gemini-2.5-pro-preview-06-05', name: 'Gemini 2.5 Pro', cost: '$$', costClass: 'mid', desc: 'Most capable Google model. Strong reasoning.' },
  ],
  openrouter: [
    { id: 'anthropic/claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', cost: '$', costClass: 'cheap', desc: 'Fastest Anthropic model via OpenRouter.' },
    { id: 'google/gemini-2.0-flash-001', name: 'Gemini 2.0 Flash', cost: '$', costClass: 'cheap', desc: 'Fastest Google model via OpenRouter.' },
    { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', cost: '$', costClass: 'cheap', desc: 'Fast OpenAI model via OpenRouter.' },
    { id: 'anthropic/claude-sonnet-4-20250514', name: 'Claude Sonnet 4', cost: '$$', costClass: 'mid', desc: 'Balanced Anthropic model via OpenRouter.' },
  ],
  custom: [],
}

const providerBaseUrls = {
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com/v1/',
  google: 'https://generativelanguage.googleapis.com/v1beta/openai/',
  openrouter: 'https://openrouter.ai/api/v1',
  custom: '',
}

const settings = reactive({
  provider: 'openai',
  apiKey: '',
  baseUrl: 'https://api.openai.com/v1',
  model: 'gpt-4o-mini',
})

const selectedProvider = computed(() => providers.find(p => p.id === settings.provider))
const availableModels = computed(() => modelCatalog[settings.provider] || [])
const keyPlaceholder = computed(() => selectedProvider.value?.keyPlaceholder || 'your-api-key')

function selectProvider(id) {
  settings.provider = id
  settings.baseUrl = providerBaseUrls[id]
  const models = modelCatalog[id]
  if (models && models.length > 0) {
    settings.model = models[0].id
  } else {
    settings.model = ''
  }
}

function selectModel(m) {
  settings.model = m.id
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
  max-width: 700px;
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

.field-hint {
  margin-top: 6px;
  font-size: 0.8rem;
  color: #999;
}

.field-link {
  color: #FF4500;
  text-decoration: none;
  font-weight: 500;
}

.field-link:hover {
  text-decoration: underline;
}

/* Provider grid */
.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.provider-card {
  border: 1px solid #e5e5e5;
  padding: 14px 12px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
}

.provider-card:hover {
  border-color: #999;
}

.provider-card.active {
  border-color: #000;
  background: #fff;
  box-shadow: 0 0 0 1px #000;
}

.provider-name {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.provider-desc {
  font-size: 0.7rem;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.3;
}

/* Model grid */
.model-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-card {
  border: 1px solid #e5e5e5;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
}

.model-card:hover {
  border-color: #999;
}

.model-card.active {
  border-color: #000;
  background: #fff;
  box-shadow: 0 0 0 1px #000;
}

.model-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.model-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.cost-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  letter-spacing: 1px;
}

.cost-badge.cheap {
  background: #e8f5e9;
  color: #2e7d32;
}

.cost-badge.mid {
  background: #fff8e1;
  color: #f57f17;
}

.cost-badge.premium {
  background: #fce4ec;
  color: #c62828;
}

.model-desc {
  font-size: 0.8rem;
  color: #666;
  line-height: 1.4;
}

/* Form inputs */
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
