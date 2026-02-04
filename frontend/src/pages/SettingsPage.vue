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
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Lookup Strategy</div>
            <q-select
              v-model="lookup.strategy"
              :options="[
                { label: 'Sequential - try providers in order', value: 'sequential' },
                { label: 'Parallel - try all at once', value: 'parallel' },
              ]"
              label="Strategy"
              outlined
              dense
              emit-value
              map-options
              class="q-mb-sm"
            />
            <div class="text-caption text-grey">Provider priority (top = highest)</div>
          </q-card-section>
        </q-card>

        <!-- OpenFoodFacts -->
        <q-card flat bordered class="q-mb-sm">
          <q-card-section>
            <div class="row items-center justify-between">
              <div class="row items-center q-gutter-sm">
                <span class="text-subtitle2">OpenFoodFacts</span>
                <q-badge color="green" label="Free" />
              </div>
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense size="sm" label="Test" @click="testProvider('openfoodfacts')" :loading="providerTesting.openfoodfacts" />
                <q-toggle v-model="lookup.openfoodfacts_enabled" />
              </div>
            </div>
            <div class="text-caption text-grey q-mt-xs">Open database with nutrition info. No API key required.</div>
            <div v-if="providerStatus.openfoodfacts" class="text-caption q-mt-xs" :class="providerStatus.openfoodfacts.ok ? 'text-green' : 'text-red'">
              {{ providerStatus.openfoodfacts.message }}
            </div>
          </q-card-section>
        </q-card>

        <!-- go-upc -->
        <q-card flat bordered class="q-mb-sm">
          <q-card-section>
            <div class="row items-center justify-between">
              <div class="row items-center q-gutter-sm">
                <span class="text-subtitle2">go-upc.com</span>
                <q-badge color="orange" label="API Key" />
                <q-badge v-if="keysConfigured.goupc" color="green" label="Key Set" />
              </div>
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense size="sm" label="Test" @click="testProvider('goupc')" :loading="providerTesting.goupc" />
                <q-toggle v-model="lookup.goupc_enabled" />
              </div>
            </div>
            <div class="text-caption text-grey q-mt-xs">Commercial UPC database with good coverage.</div>
            <q-input
              v-model="lookup.goupc_api_key"
              label="API Key"
              outlined
              dense
              type="password"
              class="q-mt-sm"
              :placeholder="keysConfigured.goupc ? 'Leave blank to keep existing' : 'Enter go-upc.com API key'"
            />
            <div v-if="providerStatus.goupc" class="text-caption q-mt-xs" :class="providerStatus.goupc.ok ? 'text-green' : 'text-red'">
              {{ providerStatus.goupc.message }}
            </div>
          </q-card-section>
        </q-card>

        <!-- UPCitemdb -->
        <q-card flat bordered class="q-mb-sm">
          <q-card-section>
            <div class="row items-center justify-between">
              <div class="row items-center q-gutter-sm">
                <span class="text-subtitle2">UPCitemdb</span>
                <q-badge color="orange" label="API Key" />
                <q-badge v-if="keysConfigured.upcitemdb" color="green" label="Key Set" />
              </div>
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense size="sm" label="Test" @click="testProvider('upcitemdb')" :loading="providerTesting.upcitemdb" />
                <q-toggle v-model="lookup.upcitemdb_enabled" />
              </div>
            </div>
            <div class="text-caption text-grey q-mt-xs">Large UPC database with free tier available.</div>
            <q-input
              v-model="lookup.upcitemdb_api_key"
              label="API Key"
              outlined
              dense
              type="password"
              class="q-mt-sm"
              :placeholder="keysConfigured.upcitemdb ? 'Leave blank to keep existing' : 'Enter UPCitemdb API key'"
            />
            <div v-if="providerStatus.upcitemdb" class="text-caption q-mt-xs" :class="providerStatus.upcitemdb.ok ? 'text-green' : 'text-red'">
              {{ providerStatus.upcitemdb.message }}
            </div>
          </q-card-section>
        </q-card>

        <!-- Brave Search -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center justify-between">
              <div class="row items-center q-gutter-sm">
                <span class="text-subtitle2">Brave Search</span>
                <q-badge color="blue" label="Fallback" />
                <q-badge v-if="keysConfigured.brave" color="green" label="Key Set" />
              </div>
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense size="sm" label="Test" @click="testProvider('brave')" :loading="providerTesting.brave" />
                <q-toggle v-model="lookup.brave_enabled" />
              </div>
            </div>
            <div class="text-caption text-grey q-mt-xs">Web search fallback for unknown products.</div>
            <q-input
              v-model="lookup.brave_api_key"
              label="API Key"
              outlined
              dense
              type="password"
              class="q-mt-sm"
              :placeholder="keysConfigured.brave ? 'Leave blank to keep existing' : 'Enter Brave Search API key'"
            />
            <q-toggle v-model="lookup.brave_use_as_fallback" label="Use as fallback only" class="q-mt-sm" />
            <div v-if="providerStatus.brave" class="text-caption q-mt-xs" :class="providerStatus.brave.ok ? 'text-green' : 'text-red'">
              {{ providerStatus.brave.message }}
            </div>
          </q-card-section>
        </q-card>

        <q-btn label="Save Lookup Settings" color="primary" @click="saveLookupSettings" :loading="saving" />
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
import { ref, reactive, onMounted } from 'vue'
import { getSettings, saveSettings, testGrocyConnection, testLookupProvider } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const tab = ref('grocy')
const saving = ref(false)
const testingGrocy = ref(false)
const grocyStatus = ref(null)

const grocy = ref({ api_url: '', api_key: '', web_url: '' })
const llm = ref({ provider_preset: 'ollama', api_url: '', api_key: '', model: '' })
const lookup = ref({
  strategy: 'sequential',
  openfoodfacts_enabled: true,
  goupc_enabled: false,
  goupc_api_key: '',
  upcitemdb_enabled: false,
  upcitemdb_api_key: '',
  brave_enabled: false,
  brave_api_key: '',
  brave_use_as_fallback: true,
})
const scanning = ref({ auto_add_enabled: false, fuzzy_match_threshold: 0.9, default_quantity_unit: 'pieces' })
const uiSettings = ref({ kiosk_mode_enabled: false })

// Track which API keys are already configured (shown as masked)
const keysConfigured = reactive({ goupc: false, upcitemdb: false, brave: false })
const providerTesting = reactive({ openfoodfacts: false, goupc: false, upcitemdb: false, brave: false })
const providerStatus = reactive({ openfoodfacts: null, goupc: null, upcitemdb: null, brave: null })

function hasKeyConfigured(val) {
  return val && typeof val === 'string' && val.startsWith('••')
}

async function loadSettings() {
  try {
    const data = await getSettings()
    const d = data.data || {}
    if (d.grocy) Object.assign(grocy.value, d.grocy)
    if (d.llm) Object.assign(llm.value, d.llm)
    if (d.lookup) {
      // Check which keys are configured before overwriting
      keysConfigured.goupc = hasKeyConfigured(d.lookup.goupc_api_key)
      keysConfigured.upcitemdb = hasKeyConfigured(d.lookup.upcitemdb_api_key)
      keysConfigured.brave = hasKeyConfigured(d.lookup.brave_api_key)
      // Don't copy masked keys to form (user should enter new or leave blank)
      const lookupData = { ...d.lookup }
      if (hasKeyConfigured(lookupData.goupc_api_key)) lookupData.goupc_api_key = ''
      if (hasKeyConfigured(lookupData.upcitemdb_api_key)) lookupData.upcitemdb_api_key = ''
      if (hasKeyConfigured(lookupData.brave_api_key)) lookupData.brave_api_key = ''
      Object.assign(lookup.value, lookupData)
    }
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

async function testProvider(provider) {
  providerTesting[provider] = true
  providerStatus[provider] = null
  try {
    const res = await testLookupProvider(provider)
    if (res.success) {
      const msg = res.product_name
        ? `Found: ${res.product_name} (${res.lookup_time_ms || 0}ms)`
        : `OK (${res.lookup_time_ms || 0}ms)`
      providerStatus[provider] = { ok: true, message: msg }
    } else {
      providerStatus[provider] = { ok: false, message: res.message || 'Test failed' }
    }
  } catch (e) {
    providerStatus[provider] = { ok: false, message: e.message || 'Test failed' }
  } finally {
    providerTesting[provider] = false
  }
}

async function saveLookupSettings() {
  saving.value = true
  try {
    const payload = {
      strategy: lookup.value.strategy,
      openfoodfacts_enabled: lookup.value.openfoodfacts_enabled,
      goupc_enabled: lookup.value.goupc_enabled,
      upcitemdb_enabled: lookup.value.upcitemdb_enabled,
      brave_enabled: lookup.value.brave_enabled,
      brave_use_as_fallback: lookup.value.brave_use_as_fallback,
    }
    // Only include API keys if user entered new ones
    if (lookup.value.goupc_api_key) payload.goupc_api_key = lookup.value.goupc_api_key
    if (lookup.value.upcitemdb_api_key) payload.upcitemdb_api_key = lookup.value.upcitemdb_api_key
    if (lookup.value.brave_api_key) payload.brave_api_key = lookup.value.brave_api_key
    
    await saveSettings('lookup', payload)
    $q.notify({ type: 'positive', message: 'Lookup settings saved' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to save settings' })
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>
