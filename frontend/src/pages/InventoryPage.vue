<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Inventory</div>
    <p class="text-caption text-grey q-mb-md">Current stock by product and location.</p>

    <q-card v-if="loading" flat bordered class="q-mb-md">
      <q-card-section>Loading...</q-card-section>
    </q-card>

    <q-table
      v-else
      :rows="entries"
      :columns="columns"
      row-key="id"
      flat
      bordered
      :rows-per-page-options="[10, 25, 50]"
      :pagination="{ rowsPerPage: 25 }"
      class="sticky-header-table"
    >
      <template v-slot:no-data>
        <div class="full-width row flex-center q-pa-md text-grey">No stock. Add products via Scan or Products.</div>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import { getMeStock } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()
const loading = ref(false)
const entries = ref([])

const columns = [
  { name: 'product_name', label: 'Product', field: 'product_name', align: 'left', sortable: true },
  { name: 'location_name', label: 'Location', field: 'location_name', align: 'left', sortable: true },
  { name: 'quantity', label: 'Qty', field: 'quantity', align: 'right', sortable: true },
  { name: 'expiration_date', label: 'Expires', field: 'expiration_date', align: 'left', sortable: true },
]

onMounted(loadStock)

async function loadStock() {
  loading.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    const data = await getMeStock(fp)
    entries.value = (data || []).map(e => ({
      ...e,
      location_name: e.location_name ?? '—',
      expiration_date: e.expiration_date ?? '—',
    }))
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load inventory' })
    entries.value = []
  } finally {
    loading.value = false
  }
}
</script>
