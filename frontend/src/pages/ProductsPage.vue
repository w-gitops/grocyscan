<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Products</div>
    <q-input
      v-model="search"
      outlined
      dense
      placeholder="Search products..."
      class="q-mb-md"
      @update:model-value="loadProducts"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>
    </q-input>
    <q-card v-if="loading" flat bordered>Loading...</q-card>
    <q-list v-else-if="products.length" bordered>
      <q-item
        v-for="p in products"
        :key="p.id"
        clickable
        @click="openDetail(p)"
      >
        <q-item-section>
          <q-item-label>{{ p.name }}</q-item-label>
          <q-item-label caption>{{ p.description || p.category || '-' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
    <q-card v-else flat bordered>No products. Add via Scan.</q-card>

    <!-- Detail dialog -->
    <q-dialog v-model="detailDialog">
      <q-card v-if="selectedProduct" style="min-width: 350px; max-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ selectedProduct.name }}</div>
          <div class="text-caption text-grey q-mb-sm">{{ selectedProduct.description || '' }}</div>
          <div class="text-caption">Category: {{ selectedProduct.category || '-' }}</div>
          <!-- Barcodes -->
          <div v-if="(selectedProduct.barcodes || []).length" class="q-mt-xs">
            <div class="text-caption text-weight-medium">Barcodes</div>
            <q-chip v-for="bc in (selectedProduct.barcodes || [])" :key="bc" dense size="sm" removable @remove="removeBarcode(bc)">
              {{ bc }}
            </q-chip>
          </div>
        </q-card-section>

        <!-- Stock by location -->
        <q-card-section v-if="detailStock.length">
          <div class="text-subtitle2 q-mb-xs">Stock by Location</div>
          <q-list dense bordered separator>
            <q-item v-for="(s, idx) in detailStock" :key="idx" dense>
              <q-item-section>
                <q-item-label>{{ s.location_name }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge color="primary">{{ s.quantity }}</q-badge>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-section v-else>
          <div class="text-grey">No stock.</div>
        </q-card-section>

        <!-- Add / Consume stock -->
        <q-card-section class="q-pt-none">
          <div class="text-subtitle2 q-mb-sm">Adjust stock</div>
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-input v-model.number="stockAddQty" type="number" min="1" dense outlined label="Qty" class="q-mb-sm" />
              <q-select
                v-model="stockAddLocationId"
                :options="locationOptions"
                label="Location"
                dense
                outlined
                emit-value
                map-options
                clearable
                class="q-mb-sm"
              />
              <q-btn label="Add" color="green" size="sm" outline class="full-width" @click="doAddStock" :loading="stockLoading" />
            </div>
            <div class="col-6">
              <q-input v-model.number="stockConsumeQty" type="number" min="1" dense outlined label="Qty" class="q-mb-sm" />
              <q-btn label="Consume" color="orange" size="sm" outline class="full-width" @click="doConsumeStock" :loading="stockLoading" />
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Edit" color="primary" @click="openEdit" />
          <q-btn flat label="Close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Edit dialog -->
    <q-dialog v-model="editDialog">
      <q-card style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">Edit Product</div>
        </q-card-section>
        <q-card-section>
          <q-input v-model="editForm.name" label="Name" outlined dense class="q-mb-sm" />
          <q-input v-model="editForm.description" label="Description" outlined dense class="q-mb-sm" />
          <q-input v-model="editForm.category" label="Category" outlined dense class="q-mb-sm" />
          <div class="text-caption q-mb-xs">Barcodes</div>
          <div class="row q-gutter-xs q-mb-sm">
            <q-chip v-for="bc in (editForm.barcodes || [])" :key="bc" dense size="sm" removable @remove="removeBarcodeInEdit(bc)">
              {{ bc }}
            </q-chip>
          </div>
          <div class="row q-gutter-sm">
            <q-input v-model="newBarcode" dense outlined label="Add barcode" class="col" placeholder="Scan or type" @keydown.enter.prevent="addBarcodeInEdit" />
            <q-btn icon="add" flat round dense color="primary" @click="addBarcodeInEdit" />
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Save" color="primary" @click="saveEdit" :loading="saving" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import {
  getMeProducts,
  getMeProductDetail,
  patchMeProduct,
  addStock,
  consumeStock,
  getMeLocations,
  addMeProductBarcode,
  removeMeProductBarcode,
} from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()
const search = ref('')
const products = ref([])
const loading = ref(false)
const detailDialog = ref(false)
const selectedProduct = ref(null)
const detailStock = ref([])
const editDialog = ref(false)
const editForm = ref({ name: '', description: '', category: '', barcodes: [] })
const saving = ref(false)
const locations = ref([])
const locationOptions = ref([])
const stockAddQty = ref(1)
const stockConsumeQty = ref(1)
const stockAddLocationId = ref(null)
const stockLoading = ref(false)
const newBarcode = ref('')

onMounted(async () => {
  loadProducts()
  const fp = await deviceStore.ensureFingerprint()
  try {
    locations.value = await getMeLocations(fp)
    locationOptions.value = locations.value.map(l => ({ label: l.name, value: l.id }))
  } catch {
    locationOptions.value = []
  }
})

async function loadProducts() {
  const fp = await deviceStore.ensureFingerprint()
  loading.value = true
  try {
    products.value = await getMeProducts(fp, search.value)
  } catch {
    products.value = []
  } finally {
    loading.value = false
  }
}

async function openDetail(product) {
  selectedProduct.value = product
  detailStock.value = []
  detailDialog.value = true
  // Fetch detail with stock
  const fp = await deviceStore.ensureFingerprint()
  try {
    const data = await getMeProductDetail(fp, product.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load detail' })
  }
}

function openEdit() {
  if (!selectedProduct.value) return
  editForm.value = {
    name: selectedProduct.value.name || '',
    description: selectedProduct.value.description || '',
    category: selectedProduct.value.category || '',
    barcodes: [...(selectedProduct.value.barcodes || [])],
  }
  newBarcode.value = ''
  editDialog.value = true
}

async function saveEdit() {
  if (!selectedProduct.value) return
  saving.value = true
  const fp = await deviceStore.ensureFingerprint()
  try {
    const updated = await patchMeProduct(fp, selectedProduct.value.id, {
      name: editForm.value.name,
      description: editForm.value.description,
      category: editForm.value.category,
    })
    selectedProduct.value = updated
    const idx = products.value.findIndex(p => p.id === updated.id)
    if (idx >= 0) products.value[idx] = updated
    editDialog.value = false
    $q.notify({ type: 'positive', message: 'Product updated' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to save' })
  } finally {
    saving.value = false
  }
}

async function doAddStock() {
  if (!selectedProduct.value || !stockAddQty.value || stockAddQty.value < 1) return
  stockLoading.value = true
  const fp = await deviceStore.ensureFingerprint()
  try {
    await addStock(fp, selectedProduct.value.id, stockAddQty.value, stockAddLocationId.value || null)
    $q.notify({ type: 'positive', message: `Added ${stockAddQty.value}` })
    const data = await getMeProductDetail(fp, selectedProduct.value.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Add failed' })
  } finally {
    stockLoading.value = false
  }
}

async function doConsumeStock() {
  if (!selectedProduct.value || !stockConsumeQty.value || stockConsumeQty.value < 1) return
  stockLoading.value = true
  const fp = await deviceStore.ensureFingerprint()
  try {
    await consumeStock(fp, selectedProduct.value.id, stockConsumeQty.value, null)
    $q.notify({ type: 'positive', message: `Consumed ${stockConsumeQty.value}` })
    const data = await getMeProductDetail(fp, selectedProduct.value.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Consume failed' })
  } finally {
    stockLoading.value = false
  }
}

async function removeBarcode(bc) {
  if (!selectedProduct.value) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await removeMeProductBarcode(fp, selectedProduct.value.id, bc)
    selectedProduct.value = { ...selectedProduct.value, barcodes: (selectedProduct.value.barcodes || []).filter(b => b !== bc) }
    $q.notify({ type: 'positive', message: 'Barcode removed' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to remove barcode' })
  }
}

async function addBarcodeInEdit() {
  const bc = (newBarcode.value || '').trim()
  if (!bc || !selectedProduct.value) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await addMeProductBarcode(fp, selectedProduct.value.id, bc)
    editForm.value.barcodes = [...(editForm.value.barcodes || []), bc]
    selectedProduct.value = { ...selectedProduct.value, barcodes: [...(selectedProduct.value.barcodes || []), bc] }
    newBarcode.value = ''
    $q.notify({ type: 'positive', message: 'Barcode added' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to add barcode' })
  }
}

async function removeBarcodeInEdit(bc) {
  if (!selectedProduct.value) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await removeMeProductBarcode(fp, selectedProduct.value.id, bc)
    editForm.value.barcodes = (editForm.value.barcodes || []).filter(b => b !== bc)
    selectedProduct.value = { ...selectedProduct.value, barcodes: (selectedProduct.value.barcodes || []).filter(b => b !== bc) }
    $q.notify({ type: 'positive', message: 'Barcode removed' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to remove barcode' })
  }
}
</script>
