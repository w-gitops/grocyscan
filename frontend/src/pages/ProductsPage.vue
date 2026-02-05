<template>
  <q-page class="q-pa-md" data-testid="products-page">
    <div class="text-h5 q-mb-md">Products</div>
    <q-input
      v-model="search"
      outlined
      dense
      placeholder="Search products..."
      class="q-mb-md"
      @update:model-value="loadProducts"
      data-testid="products-search"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>
    </q-input>
    <q-card v-if="loading" flat bordered data-testid="products-loading">Loading...</q-card>
    <q-list v-else-if="products.length" bordered data-testid="products-list">
      <q-item
        v-for="p in products"
        :key="p.id"
        clickable
        @click="openDetail(p)"
        data-testid="product-card"
      >
        <q-item-section>
          <q-item-label>{{ p.name }}</q-item-label>
          <q-item-label caption>{{ p.description || p.category || '-' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
    <q-card v-else flat bordered data-testid="products-empty">No products. Add via Scan.</q-card>

    <!-- Detail dialog -->
    <q-dialog v-model="detailDialog" data-testid="product-detail-dialog">
      <q-card v-if="selectedProduct" style="min-width: 350px; max-width: 500px">
        <q-card-section>
          <div class="text-h6" data-testid="product-detail-name">{{ selectedProduct.name }}</div>
          <div class="text-caption text-grey q-mb-sm">{{ selectedProduct.description || '' }}</div>
          <div class="text-caption">Category: {{ selectedProduct.category || '-' }}</div>
          <!-- Barcodes -->
          <div v-if="(selectedProduct.barcodes || []).length" class="q-mt-xs" data-testid="product-barcodes-list">
            <div class="text-caption text-weight-medium">Barcodes</div>
            <q-chip v-for="bc in (selectedProduct.barcodes || [])" :key="bc" dense size="sm" removable @remove="removeBarcode(bc)" data-testid="product-barcode-chip">
              {{ bc }}
            </q-chip>
          </div>
        </q-card-section>

        <!-- Stock entries list -->
        <q-card-section v-if="detailStock.length" data-testid="stock-entry-list">
          <div class="text-subtitle2 q-mb-xs">Stock Entries</div>
          <q-list dense bordered separator>
            <q-item
              v-for="(s, idx) in detailStock"
              :key="idx"
              dense
              :data-testid="`stock-entry-row-${idx}`"
            >
              <q-item-section avatar>
                <q-icon v-if="s.open" name="open_in_new" color="orange" size="sm">
                  <q-tooltip>Opened</q-tooltip>
                </q-icon>
                <q-icon v-else name="inventory" color="grey" size="sm" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ s.location_name || 'Unspecified' }}</q-item-label>
                <q-item-label caption>
                  <span v-if="s.expiration_date" :class="isExpiringSoon(s.expiration_date) ? 'text-warning' : (isExpired(s.expiration_date) ? 'text-negative' : '')">
                    Exp: {{ s.expiration_date }}
                  </span>
                  <span v-if="s.price"> · ${{ s.price }}</span>
                  <span v-if="s.note"> · {{ s.note }}</span>
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="row items-center q-gutter-xs">
                  <q-badge color="primary">{{ s.quantity }}</q-badge>
                  <q-btn
                    flat
                    round
                    dense
                    size="sm"
                    icon="swap_horiz"
                    @click="openMoveDialog(s)"
                    data-testid="stock-move-btn"
                  >
                    <q-tooltip>Move to different location</q-tooltip>
                  </q-btn>
                  <q-btn
                    v-if="!s.open"
                    flat
                    round
                    dense
                    size="sm"
                    icon="open_in_new"
                    @click="markOpen(s)"
                  >
                    <q-tooltip>Mark as opened</q-tooltip>
                  </q-btn>
                </div>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-section v-else>
          <div class="text-grey">No stock.</div>
        </q-card-section>

        <!-- Inventory correction button -->
        <q-card-section class="q-pt-none">
          <q-btn
            outline
            color="secondary"
            label="Set Inventory"
            icon="calculate"
            size="sm"
            @click="openInventoryDialog"
            data-testid="inventory-correction-btn"
          />
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
          <q-btn flat label="Edit" color="primary" @click="openEdit" data-testid="product-edit-button" />
          <q-btn flat label="Close" v-close-popup data-testid="product-detail-close" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Edit dialog -->
    <q-dialog v-model="editDialog" data-testid="product-edit-dialog">
      <q-card style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">Edit Product</div>
        </q-card-section>
        <q-card-section>
          <q-input v-model="editForm.name" label="Name" outlined dense class="q-mb-sm" data-testid="product-name-input" />
          <q-input v-model="editForm.description" label="Description" outlined dense class="q-mb-sm" data-testid="product-description-input" />
          <q-input v-model="editForm.category" label="Category" outlined dense class="q-mb-sm" data-testid="product-category-input" />
          <div class="text-caption q-mb-xs">Barcodes</div>
          <div class="row q-gutter-xs q-mb-sm">
            <q-chip v-for="bc in (editForm.barcodes || [])" :key="bc" dense size="sm" removable @remove="removeBarcodeInEdit(bc)">
              {{ bc }}
            </q-chip>
          </div>
          <div class="row q-gutter-sm">
            <q-input v-model="newBarcode" dense outlined label="Add barcode" class="col" placeholder="Scan or type" @keydown.enter.prevent="addBarcodeInEdit" data-testid="product-barcode-input" />
            <q-btn icon="add" flat round dense color="primary" @click="addBarcodeInEdit" data-testid="product-add-barcode-button" />
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup data-testid="product-cancel-button" />
          <q-btn flat label="Save" color="primary" @click="saveEdit" :loading="saving" data-testid="product-save-button" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Move stock dialog -->
    <q-dialog v-model="moveDialog" data-testid="stock-move-dialog">
      <q-card style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">Move Stock</div>
          <div class="text-caption">{{ movingEntry?.location_name || 'Unspecified' }} → ?</div>
        </q-card-section>
        <q-card-section>
          <q-select
            v-model="moveTargetLocation"
            :options="locationOptions"
            label="Move to location"
            outlined
            dense
            emit-value
            map-options
            data-testid="stock-move-location-select"
          />
          <q-input
            v-model.number="moveQuantity"
            type="number"
            :max="movingEntry?.quantity"
            min="1"
            label="Quantity to move"
            outlined
            dense
            class="q-mt-sm"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Move"
            color="primary"
            @click="doMoveStock"
            :loading="moveLoading"
            data-testid="stock-move-confirm-btn"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Inventory correction dialog -->
    <q-dialog v-model="inventoryDialog" data-testid="inventory-correction-dialog">
      <q-card style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">Set Inventory</div>
          <div class="text-caption">Current total: {{ totalStock }}</div>
        </q-card-section>
        <q-card-section>
          <q-input
            v-model.number="inventoryNewAmount"
            type="number"
            min="0"
            label="Set total stock to"
            outlined
            dense
            data-testid="inventory-amount-input"
          />
          <q-select
            v-model="inventoryLocationId"
            :options="locationOptions"
            label="Location (optional)"
            outlined
            dense
            emit-value
            map-options
            clearable
            class="q-mt-sm"
          />
          <div v-if="inventoryDiff !== 0" class="text-caption q-mt-sm" :class="inventoryDiff > 0 ? 'text-positive' : 'text-negative'">
            {{ inventoryDiff > 0 ? `+${inventoryDiff}` : inventoryDiff }} adjustment
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Confirm"
            color="primary"
            @click="doInventoryCorrection"
            :loading="inventoryLoading"
            data-testid="inventory-confirm-btn"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
  transferStock,
  inventoryStock,
  openStock,
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

// Phase 3.5: Move stock dialog
const moveDialog = ref(false)
const movingEntry = ref(null)
const moveTargetLocation = ref(null)
const moveQuantity = ref(1)
const moveLoading = ref(false)

// Phase 3.5: Inventory correction dialog
const inventoryDialog = ref(false)
const inventoryNewAmount = ref(0)
const inventoryLocationId = ref(null)
const inventoryLoading = ref(false)

// Computed: total stock
const totalStock = computed(() => {
  return detailStock.value.reduce((sum, s) => sum + (Number(s.quantity) || 0), 0)
})

// Computed: inventory adjustment difference
const inventoryDiff = computed(() => {
  return (inventoryNewAmount.value || 0) - totalStock.value
})

// Helper: check if date is expiring soon (within 7 days)
function isExpiringSoon(dateStr) {
  if (!dateStr) return false
  const exp = new Date(dateStr)
  const now = new Date()
  const diff = (exp - now) / (1000 * 60 * 60 * 24)
  return diff > 0 && diff <= 7
}

// Helper: check if expired
function isExpired(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

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
  } catch (e) {
    products.value = []
    $q.notify({ type: 'negative', message: e.message || 'Failed to load products' })
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

// Phase 3.5: Open move dialog
function openMoveDialog(entry) {
  movingEntry.value = entry
  moveTargetLocation.value = null
  moveQuantity.value = entry.quantity || 1
  moveDialog.value = true
}

// Phase 3.5: Execute move stock
async function doMoveStock() {
  if (!selectedProduct.value || !movingEntry.value || !moveTargetLocation.value) {
    $q.notify({ type: 'warning', message: 'Select a destination location' })
    return
  }
  if (moveQuantity.value < 1 || moveQuantity.value > movingEntry.value.quantity) {
    $q.notify({ type: 'warning', message: 'Invalid quantity' })
    return
  }
  moveLoading.value = true
  const fp = await deviceStore.ensureFingerprint()
  try {
    await transferStock(
      fp,
      selectedProduct.value.id,
      movingEntry.value.location_id,
      moveTargetLocation.value,
      moveQuantity.value
    )
    $q.notify({ type: 'positive', message: 'Stock moved' })
    moveDialog.value = false
    // Refresh detail
    const data = await getMeProductDetail(fp, selectedProduct.value.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Move failed' })
  } finally {
    moveLoading.value = false
  }
}

// Phase 3.5: Mark stock as opened
async function markOpen(entry) {
  if (!entry || !entry.id) return
  const fp = await deviceStore.ensureFingerprint()
  try {
    await openStock(fp, entry.id)
    $q.notify({ type: 'positive', message: 'Marked as opened' })
    // Refresh detail
    const data = await getMeProductDetail(fp, selectedProduct.value.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to mark as opened' })
  }
}

// Phase 3.5: Open inventory correction dialog
function openInventoryDialog() {
  inventoryNewAmount.value = totalStock.value
  inventoryLocationId.value = null
  inventoryDialog.value = true
}

// Phase 3.5: Execute inventory correction
async function doInventoryCorrection() {
  if (!selectedProduct.value) return
  if (inventoryNewAmount.value < 0) {
    $q.notify({ type: 'warning', message: 'Amount cannot be negative' })
    return
  }
  inventoryLoading.value = true
  const fp = await deviceStore.ensureFingerprint()
  try {
    await inventoryStock(
      fp,
      selectedProduct.value.id,
      inventoryNewAmount.value,
      inventoryLocationId.value
    )
    $q.notify({ type: 'positive', message: 'Inventory updated' })
    inventoryDialog.value = false
    // Refresh detail
    const data = await getMeProductDetail(fp, selectedProduct.value.id)
    if (data.product) selectedProduct.value = data.product
    detailStock.value = data.stock || []
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Inventory correction failed' })
  } finally {
    inventoryLoading.value = false
  }
}
</script>
