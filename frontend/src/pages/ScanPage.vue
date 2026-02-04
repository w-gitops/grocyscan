<template>
  <q-page class="q-pa-md">
    <h1 class="text-h5 q-mb-md">Scan</h1>

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
        <div v-show="cameraActive" id="scanner-container" class="q-mb-sm" style="width: 100%; max-width: 400px; min-height: 300px; margin: 0 auto; background: #000;"></div>

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

    <!-- Product Review popup -->
    <q-dialog v-model="reviewDialog">
      <q-card style="min-width: 350px; max-width: 450px">
        <q-card-section>
          <div class="row items-center q-gutter-sm">
            <div class="text-h6">{{ reviewData.in_homebot ? 'In Inventory' : reviewData.found ? 'Lookup Found' : 'New Product' }}</div>
            <q-badge v-if="reviewData.in_homebot" color="green" label="In Homebot" />
            <q-badge v-else-if="reviewData.found" color="blue" label="From lookup" />
          </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <!-- Product image if available -->
          <div v-if="reviewData.image_url" class="q-mb-md text-center">
            <q-img :src="reviewData.image_url" style="max-height: 120px; max-width: 120px" fit="contain" />
          </div>
          
          <div class="text-subtitle1 q-mb-xs">{{ reviewData.name || reviewData.barcode }}</div>
          <div v-if="reviewData.brand" class="text-caption text-grey-7 q-mb-xs">{{ reviewData.brand }}</div>
          <div v-if="reviewData.category" class="text-caption text-grey q-mb-xs">{{ reviewData.category }}</div>
          <div v-if="reviewData.barcode" class="text-caption text-grey q-mb-sm">Barcode: {{ reviewData.barcode }}</div>
          
          <!-- Lookup source info -->
          <div v-if="reviewData.lookup_provider" class="text-caption text-grey q-mb-md">
            Found via {{ reviewData.lookup_provider }} ({{ reviewData.lookup_time_ms }}ms)
          </div>
          
          <q-input
            v-if="!reviewData.found"
            v-model="reviewData.name"
            label="Product name"
            outlined
            dense
            placeholder="Enter name for new product"
            class="q-mb-sm"
          />
          <q-input
            v-model.number="reviewData.quantity"
            label="Quantity"
            type="number"
            min="1"
            outlined
            dense
            class="q-mb-sm"
          />
          <q-select
            v-if="locations.length"
            v-model="reviewData.location_id"
            :options="locationOptions"
            label="Location"
            outlined
            dense
            emit-value
            map-options
            clearable
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            v-if="reviewData.in_homebot"
            flat
            :label="actionMode === 'consume' ? 'Consume' : 'Add to Stock'"
            :color="actionMode === 'consume' ? 'orange' : 'primary'"
            @click="confirmReview"
            :loading="reviewLoading"
          />
          <q-btn
            v-else-if="reviewData.found || reviewData.name"
            flat
            label="Create in Homebot & Add to Stock"
            color="primary"
            @click="createAndAddToHomebot"
            :loading="reviewLoading"
          />
          <q-btn
            v-else
            flat
            label="Enter name below, then Create & Add"
            color="grey"
            disable
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useDeviceStore } from '../stores/device'
import {
  getMeDevice,
  registerDevice as apiRegisterDevice,
  patchMeDevice,
  getProductByBarcode,
  scanBarcode,
  confirmScan,
  addStock,
  consumeStock,
  createMeProduct,
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
const reviewDialog = ref(false)
const reviewLoading = ref(false)
const reviewData = ref({ barcode: '', name: '', found: false, in_homebot: false, product_id: null, quantity: 1, location_id: null })
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
    // Show the container first so html5-qrcode can find it
    cameraActive.value = true
    await nextTick()
    
    html5QrCode = new Html5Qrcode('scanner-container')
    
    // Try back camera first, then fall back to any camera
    try {
      await html5QrCode.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 150 } },
        onCameraScan,
        () => {} // ignore errors during scanning
      )
    } catch (backCamError) {
      console.warn('Back camera failed, trying any camera:', backCamError)
      // Try any available camera
      await html5QrCode.start(
        { facingMode: 'user' },
        { fps: 10, qrbox: { width: 250, height: 150 } },
        onCameraScan,
        () => {}
      )
    }
  } catch (e) {
    cameraActive.value = false
    console.error('Camera error:', e)
    
    // Provide specific error messages
    let msg = 'Camera not available.'
    if (e.name === 'NotAllowedError' || e.message?.includes('denied') || e.message?.includes('Permission')) {
      msg = 'Camera permission denied. Please allow camera access in your browser settings and reload the page.'
    } else if (e.name === 'NotFoundError' || e.message?.includes('not found')) {
      msg = 'No camera found on this device.'
    } else if (e.name === 'NotReadableError' || e.message?.includes('in use')) {
      msg = 'Camera is in use by another application.'
    } else if (!window.isSecureContext) {
      msg = 'Camera requires HTTPS. Please access this page via https://.'
    }
    
    $q.notify({ type: 'negative', message: msg, timeout: 5000 })
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
    // First check if already in Homebot inventory
    const homebotProduct = await getProductByBarcode(fp, code)
    if (homebotProduct && homebotProduct.product_id) {
      productName.value = homebotProduct.name
      productId.value = homebotProduct.product_id
      reviewData.value = {
        barcode: code,
        name: homebotProduct.name,
        found: true,
        in_homebot: true,
        product_id: homebotProduct.product_id,
        quantity: 1,
        location_id: defaultLocationId.value,
      }
      reviewDialog.value = true
      return
    }
    // Not in Homebot: try external lookup
    const res = await scanBarcode(code)
    if (res.found && res.product) {
      productName.value = res.product.name
      productId.value = null
      reviewData.value = {
        barcode: res.barcode,
        name: res.product.name,
        brand: res.product.brand,
        description: res.product.description,
        category: res.product.category,
        image_url: res.product.image_url,
        found: true,
        in_homebot: false,
        product_id: null,
        is_new: res.product.is_new,
        existing_in_grocy: res.existing_in_grocy,
        scan_id: res.scan_id,
        quantity: 1,
        location_id: defaultLocationId.value,
        lookup_provider: res.lookup_provider,
        lookup_time_ms: res.lookup_time_ms,
      }
      reviewDialog.value = true
    } else {
      productName.value = ''
      productId.value = null
      reviewData.value = {
        barcode: code,
        name: '',
        found: false,
        in_homebot: false,
        product_id: null,
        quantity: 1,
        location_id: defaultLocationId.value,
      }
      reviewDialog.value = true
    }
  } catch (e) {
    addRecentScan(code, null, false)
    $q.notify({ type: 'negative', message: e.message || 'Lookup failed' })
  }
}

async function confirmReview() {
  if (!reviewData.value.in_homebot || !reviewData.value.product_id) return
  reviewLoading.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    const qty = reviewData.value.quantity || 1
    const locId = reviewData.value.location_id || null
    if (actionMode.value === 'consume') {
      await consumeStock(fp, reviewData.value.product_id, qty, locId)
      $q.notify({ type: 'positive', message: `Consumed ${qty}` })
    } else {
      await addStock(fp, reviewData.value.product_id, qty, locId)
      $q.notify({ type: 'positive', message: `Added ${qty}` })
    }
    addRecentScan(reviewData.value.barcode, reviewData.value.name, true)
    reviewDialog.value = false
    barcode.value = ''
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Action failed' })
    addRecentScan(reviewData.value.barcode, reviewData.value.name, false)
  } finally {
    reviewLoading.value = false
  }
}

async function createAndAddToHomebot() {
  const name = (reviewData.value.name || reviewData.value.barcode || '').trim()
  if (!name) {
    $q.notify({ type: 'warning', message: 'Enter a product name' })
    return
  }
  reviewLoading.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    await createMeProduct(fp, {
      name,
      barcode: reviewData.value.barcode || null,
      description: reviewData.value.description || null,
      category: reviewData.value.category || null,
      quantity: reviewData.value.quantity || 1,
      location_id: reviewData.value.location_id || null,
    })
    $q.notify({ type: 'positive', message: 'Product created and added to stock' })
    addRecentScan(reviewData.value.barcode, name, true)
    reviewDialog.value = false
    barcode.value = ''
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Create failed' })
    addRecentScan(reviewData.value.barcode, name, false)
  } finally {
    reviewLoading.value = false
  }
}

function isHomeBotUuid(v) {
  if (v == null) return false
  const s = String(v)
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s)
}

function getConfirmPayload(qty) {
  const name = (reviewData.value?.name || reviewData.value?.barcode || barcode.value || 'Product').trim() || 'Product'
  return {
    name,
    description: reviewData.value?.description ?? '',
    category: reviewData.value?.category ?? '',
    brand: reviewData.value?.brand ?? '',
    quantity: qty,
    create_in_grocy: true,
    use_llm_enhancement: false,
  }
}

async function quickAdd(qty) {
  if (!productName.value && !reviewData.value?.barcode && !productId.value) return
  try {
    if (isHomeBotUuid(productId.value)) {
      const fp = await deviceStore.ensureFingerprint()
      await addStock(fp, productId.value, qty)
      $q.notify({ type: 'positive', message: `Added ${qty}` })
      return
    }
    const barcodeToUse = reviewData.value?.barcode || barcode.value?.trim()
    if (barcodeToUse) {
      const payload = getConfirmPayload(qty)
      const fresh = await scanBarcode(barcodeToUse)
      if (!fresh.scan_id) throw new Error('Lookup did not return a session')
      const result = await confirmScan(fresh.scan_id, payload)
      if (result.success) {
        $q.notify({ type: 'positive', message: `Added ${qty}` })
        productName.value = ''
        productId.value = null
        reviewData.value = { ...reviewData.value, scan_id: null }
      } else {
        throw new Error(result.message || 'Add failed')
      }
      return
    }
    $q.notify({ type: 'info', message: 'Use the review dialog to add this product first' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Add failed' })
  }
}

async function quickConsume(qty) {
  if (!productId.value) return
  if (reviewData.value?.scan_id) {
    $q.notify({ type: 'info', message: 'Add from the review dialog first; then consume from Products' })
    return
  }
  if (!isHomeBotUuid(productId.value)) {
    $q.notify({ type: 'info', message: 'Consume is available for products already in your inventory' })
    return
  }
  const fp = await deviceStore.ensureFingerprint()
  try {
    await consumeStock(fp, productId.value, qty)
    $q.notify({ type: 'positive', message: `Consumed ${qty}` })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Consume failed' })
  }
}
</script>
