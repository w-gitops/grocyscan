<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Settings</div>

    <q-tabs v-model="tab" dense align="left" class="q-mb-md">
      <q-tab name="grocy" label="Grocy" />
      <q-tab name="llm" label="LLM" />
      <q-tab name="lookup" label="Lookup" />
      <q-tab name="scanning" label="Scanning" />
      <q-tab name="ui" label="UI" />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <!-- Grocy -->
      <q-tab-panel name="grocy">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Grocy Connection</div>
            <q-input v-model="grocy.api_url" label="API URL" outlined dense class="q-mb-sm" />
            <q-input v-model="grocy.api_key" label="API Key" outlined dense type="password" class="q-mb-sm" placeholder="Leave blank to keep existing" />
            <q-input v-model="grocy.web_url" label="Web URL" outlined dense class="q-mb-md" />
            <div class="row q-gutter-sm">
              <q-btn label="Test Connection" outline @click="testGrocy" :loading="testingGrocy" />
              <q-btn label="Save" color="primary" @click="saveSection('grocy', grocy)" :loading="saving" />
            </div>
            <div v-if="grocyStatus" class="q-mt-sm" :class="grocyStatus.ok ? 'text-green' : 'text-red'">
              {{ grocyStatus.message }}
            </div>
          </q-card-section>
        </q-card>
      </q-tab-panel>

      <!-- LLM -->
      <q-tab-panel name="llm">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">LLM Configuration</div>
            <q-select v-model="llm.provider_preset" :options="['openai', 'anthropic', 'ollama', 'generic']" label="Provider Preset" outlined dense class="q-mb-sm" />
            <q-input v-model="llm.api_url" label="API URL" outlined dense class="q-mb-sm" />
            <q-input v-model="llm.api_key" label="API Key" outlined dense type="password" class="q-mb-sm" placeholder="Leave blank to keep existing" />
            <q-input v-model="llm.model" label="Model" outlined dense class="q-mb-md" />
            <q-btn label="Save" color="primary" @click="saveSection('llm', llm)" :loading="saving" />
          </q-card-section>
        </q-card>
      </q-tab-panel>

      <!-- Lookup -->
      <q-tab-panel name="lookup">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Lookup Providers</div>
            <q-select v-model="lookup.strategy" :options="['sequential', 'parallel', 'first_match']" label="Strategy" outlined dense class="q-mb-sm" />
            <q-input v-model="lookup.provider_order" label="Provider Order (comma-separated)" outlined dense class="q-mb-sm" />
            <q-input v-model="lookup.timeout_seconds" label="Timeout (seconds)" outlined dense type="number" class="q-mb-md" />
            <q-btn label="Save" color="primary" @click="saveSection('lookup', lookup)" :loading="saving" />
          </q-card-section>
        </q-card>
      </q-tab-panel>

      <!-- Scanning -->
      <q-tab-panel name="scanning">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Scanning Behavior</div>
            <q-toggle v-model="scanning.auto_add_enabled" label="Auto-add products" class="q-mb-sm" />
            <q-input v-model="scanning.fuzzy_match_threshold" label="Fuzzy Match Threshold" outlined dense type="number" step="0.1" class="q-mb-sm" />
            <q-input v-model="scanning.default_quantity_unit" label="Default Quantity Unit" outlined dense class="q-mb-md" />
            <q-btn label="Save" color="primary" @click="saveSection('scanning', scanning)" :loading="saving" />
          </q-card-section>
        </q-card>
      </q-tab-panel>

      <!-- UI -->
      <q-tab-panel name="ui">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">UI Settings</div>
            <q-toggle v-model="uiSettings.kiosk_mode_enabled" label="Kiosk Mode" class="q-mb-md" />
            <q-btn label="Save" color="primary" @click="saveSection('ui', uiSettings)" :loading="saving" />
          </q-card-section>
        </q-card>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, saveSettings, testGrocyConnection } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const tab = ref('grocy')
const saving = ref(false)
const testingGrocy = ref(false)
const grocyStatus = ref(null)

const grocy = ref({ api_url: '', api_key: '', web_url: '' })
const llm = ref({ provider_preset: 'ollama', api_url: '', api_key: '', model: '' })
const lookup = ref({ strategy: 'sequential', provider_order: '', timeout_seconds: 10 })
const scanning = ref({ auto_add_enabled: false, fuzzy_match_threshold: 0.9, default_quantity_unit: 'pieces' })
const uiSettings = ref({ kiosk_mode_enabled: false })

async function loadSettings() {
  try {
    const data = await getSettings()
    const d = data.data || {}
    if (d.grocy) Object.assign(grocy.value, d.grocy)
    if (d.llm) Object.assign(llm.value, d.llm)
    if (d.lookup) Object.assign(lookup.value, d.lookup)
    if (d.scanning) Object.assign(scanning.value, d.scanning)
    if (d.ui) Object.assign(uiSettings.value, d.ui)
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load settings' })
  }
}

async function saveSection(section, values) {
  saving.value = true
  try {
    // Filter out empty api_key to avoid overwriting
    const payload = { ...values }
    if (section === 'grocy' && !payload.api_key) delete payload.api_key
    if (section === 'llm' && !payload.api_key) delete payload.api_key
    await saveSettings(section, payload)
    $q.notify({ type: 'positive', message: 'Settings saved' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to save settings' })
  } finally {
    saving.value = false
  }
}

async function testGrocy() {
  testingGrocy.value = true
  grocyStatus.value = null
  try {
    const res = await testGrocyConnection()
    grocyStatus.value = { ok: res.success, message: res.message || (res.success ? 'Connected' : 'Failed') }
  } catch (e) {
    grocyStatus.value = { ok: false, message: e.message || 'Connection failed' }
  } finally {
    testingGrocy.value = false
  }
}

onMounted(loadSettings)
</script>
