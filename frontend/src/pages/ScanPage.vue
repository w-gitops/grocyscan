<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Scan</div>

    <!-- Device registration prompt -->
    <q-banner v-if="showDevicePrompt" class="bg-primary text-white rounded-borders q-mb-md">
      <template v-slot:action>
        <q-btn flat label="Register" @click="openDeviceDialog" />
      </template>
      Register this device to use Homebot inventory.
    </q-banner>

    <!-- Action mode selector -->
    <q-btn-toggle
      v-model="actionMode"
      toggle-color="primary"
      :options="[
        { label: 'Add Stock', value: 'add' },
        { label: 'Consume', value: 'consume' },
        { label: 'Transfer', value: 'transfer' },
      ]"
      class="q-mb-md"
      spread
      @update:model-value="onActionModeChange"
    />

    <!-- Default location selector -->
    <q-select
      v-if="locations.length"
      v-model="defaultLocationId"
      :options="locationOptions"
      label="Default Location"
      outlined
      dense
      emit-value
      map-options
      clearable
      class="q-mb-md"
      @update:model-value="onDefaultLocationChange"
    />

    <q-card flat bordered>
      <q-card-section>
        <!-- Camera scanner toggle -->
        <div class="row items-center q-mb-sm">
          <q-btn
            :icon="cameraActive ? 'videocam_off' : 'qr_code_scanner'"
            :label="cameraActive ? 'Stop Camera' : 'Scan with Camera'"
            :color="cameraActive ? 'negative' : 'secondary'"
            outline
            class="full-width q-mb-sm"
            @click="toggleCamera"
          />
        </div>

        <!-- Camera preview -->
        <div v-show="cameraActive" id="scanner-container" class="q-mb-sm" style="width: 100%; max-width: 400px; margin: 0 auto;"></div>

        <q-input
          v-model="barcode"
          label="Barcode"
          outlined
          dense
          placeholder="Scan or enter barcode..."
          @keydown.enter="onLookup"
          class="q-mb-sm"
        >
          <template v-slot:append>
            <q-btn icon="search" flat round dense @click="onLookup" />
          </template>
        </q-input>
        <q-btn label="Look up" color="primary" @click="onLookup" class="full-width" />
      </q-card-section>
    </q-card>

    <!-- Result -->
    <q-card v-if="productName" flat bordered class="q-mt-md">
      <q-card-section>
        <div class="text-subtitle1">{{ productName }}</div>
        <div class="row q-gutter-sm q-mt-sm">
          <q-btn label="+1" color="green" @click="quickAdd(1)" />
          <q-btn label="-1" color="orange" @click="quickConsume(1)" />
        </div>
      </q-card-section>
    </q-card>

    <!-- Recent scans -->
    <q-card v-if="recentScans.length" flat bordered class="q-mt-md">
      <q-card-section>
        <div class="text-subtitle2 q-mb-sm">Recent Scans</div>
        <q-list dense>
          <q-item v-for="(scan, idx) in recentScans" :key="idx" dense>
            <q-item-section avatar>
              <q-icon :name="scan.success ? 'check_circle' : 'info'" :color="scan.success ? 'green' : 'grey'" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ scan.name || scan.barcode }}</q-item-label>
              <q-item-label caption>{{ scan.barcode }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
    </q-card>

    <!-- Device registration dialog -->
    <q-dialog v-model="deviceDialog">
      <q-card style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">Register device</div>
        </q-card-section>
        <q-card-section>
          <q-input v-model="deviceName" label="Device name" outlined dense class="q-mb-sm" />
          <q-btn label="Register" color="primary" class="full-width" @click="registerDevice" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useDeviceStore } from '../stores/device'
import {
  getMeDevice,
  registerDevice as apiRegisterDevice,
  patchMeDevice,
  getProductByBarcode,
  addStock,
  consumeStock,
  getMeLocations,
} from '../services/api'
import { useQuasar } from 'quasar'
import { Html5Qrcode } from 'html5-qrcode'

const $q = useQuasar()
const deviceStore = useDeviceStore()

const barcode = ref('')
const productName = ref('')
const productId = ref(null)
const showDevicePrompt = ref(false)
const deviceDialog = ref(false)
const deviceName = ref('')
const actionMode = ref('add')
const recentScans = ref([])
const locations = ref([])
const defaultLocationId = ref(null)
const cameraActive = ref(false)
let html5QrCode = null

const locationOptions = computed(() => locations.value.map(l => ({ label: l.name, value: l.id })))

const RECENT_SCANS_KEY = 'homebot_recent_scans'
const MAX_RECENT_SCANS = 5

function loadRecentScans() {
  try {
    const stored = localStorage.getItem(RECENT_SCANS_KEY)
    if (stored) recentScans.value = JSON.parse(stored).slice(0, MAX_RECENT_SCANS)
  } catch {
    recentScans.value = []
  }
}

function saveRecentScans() {
  try {
    localStorage.setItem(RECENT_SCANS_KEY, JSON.stringify(recentScans.value.slice(0, MAX_RECENT_SCANS)))
  } catch {
    // ignore storage errors
  }
}

function addRecentScan(barcode, name, success) {
  recentScans.value = [{ barcode, name, success }, ...recentScans.value.filter(s => s.barcode !== barcode)].slice(0, MAX_RECENT_SCANS)
  saveRecentScans()
}

async function loadLocations() {
  const fp = await deviceStore.ensureFingerprint()
  try {
    locations.value = await getMeLocations(fp)
  } catch {
    locations.value = []
  }
}

onMounted(async () => {
  loadRecentScans()
  const fp = await deviceStore.ensureFingerprint()
  try {
    const device = await getMeDevice(fp)
    if (!device) {
      showDevicePrompt.value = true
    } else {
      // Set action mode from device settings
      const mode = (device.default_action || 'add_stock').replace('_stock', '')
      actionMode.value = ['add', 'consume', 'transfer'].includes(mode) ? mode : 'add'
      defaultLocationId.value = device.default_location_id || null
    }
  } catch {
    showDevicePrompt.value = true
  }
  await loadLocations()
})

onUnmounted(() => {
  stopCamera()
})

async function toggleCamera() {
  if (cameraActive.value) {
    await stopCamera()
  } else {
    await startCamera()
  }
}

async function startCamera() {
  try {
    html5QrCode = new Html5Qrcode('scanner-container')
    await html5QrCode.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 150 } },
      onCameraScan,
      () => {} // ignore errors during scanning
    )
    cameraActive.value = true
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Camera access denied or not available. HTTPS required.' })
  }
}

async function stopCamera() {
  if (html5QrCode && cameraActive.value) {
    try {
      await html5QrCode.stop()
    } catch {
      // ignore
    }
  }
  cameraActive.value = false
}

function onCameraScan(decodedText) {
  barcode.value = decodedText
  stopCamera()
  onLookup()
}

async function onActionModeChange(mode) {
  const fp = await deviceStore.ensureFingerprint()
  try {
    await patchMeDevice(fp, { default_action: mode === 'add' ? 'add_stock' : mode })
  } catch {
    // ignore - mode still changes locally
  }
}

async function onDefaultLocationChange(locId) {
  const fp = await deviceStore.ensureFingerprint()
  try {
    await patchMeDevice(fp, { default_location_id: locId || null })
  } catch {
    // ignore
  }
}

function openDeviceDialog() {
  deviceName.value = deviceStore.deviceName || 'My Device'
  deviceDialog.value = true
}

async function registerDevice() {
  const fp = await deviceStore.ensureFingerprint()
  try {
    await apiRegisterDevice(fp, deviceName.value)
    deviceStore.setDevice(deviceName.value)
    showDevicePrompt.value = false
    deviceDialog.value = false
    $q.notify({ type: 'positive', message: 'Device registered' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Registration failed' })
  }
}

async function onLookup() {
  const code = barcode.value?.trim()
  if (!code) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    const res = await getProductByBarcode(fp, code)
    if (res) {
      productName.value = res.name
      productId.value = res.product_id
      addRecentScan(code, res.name, true)
      // Auto-execute based on action mode
      if (actionMode.value === 'add') {
        await quickAdd(1)
      } else if (actionMode.value === 'consume') {
        await quickConsume(1)
      }
      // transfer mode: just show result, user can pick action
    } else {
      productName.value = ''
      productId.value = null
      addRecentScan(code, null, false)
      $q.notify({ type: 'info', message: 'Product not in Homebot inventory' })
    }
  } catch (e) {
    addRecentScan(code, null, false)
    $q.notify({ type: 'negative', message: e.message || 'Lookup failed' })
  }
}

async function quickAdd(qty) {
  if (!productId.value) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await addStock(fp, productId.value, qty)
    $q.notify({ type: 'positive', message: `Added ${qty}` })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Add failed' })
  }
}

async function quickConsume(qty) {
  if (!productId.value) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await consumeStock(fp, productId.value, qty)
    $q.notify({ type: 'positive', message: `Consumed ${qty}` })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Consume failed' })
  }
}
</script>
