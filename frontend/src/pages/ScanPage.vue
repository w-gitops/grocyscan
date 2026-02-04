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

    <q-card flat bordered>
      <q-card-section>
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
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import {
  getMeDevice,
  registerDevice as apiRegisterDevice,
  getProductByBarcode,
  addStock,
  consumeStock,
} from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()

const barcode = ref('')
const productName = ref('')
const productId = ref(null)
const showDevicePrompt = ref(false)
const deviceDialog = ref(false)
const deviceName = ref('')

onMounted(async () => {
  const fp = await deviceStore.ensureFingerprint()
  try {
    const device = await getMeDevice(fp)
    if (!device) showDevicePrompt.value = true
  } catch {
    showDevicePrompt.value = true
  }
})

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
    } else {
      productName.value = ''
      productId.value = null
      $q.notify({ type: 'info', message: 'Product not in Homebot inventory' })
    }
  } catch (e) {
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
