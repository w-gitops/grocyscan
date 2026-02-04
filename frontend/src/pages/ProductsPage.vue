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
        @click="selectedProduct = p; detailDialog = true"
      >
        <q-item-section>
          <q-item-label>{{ p.name }}</q-item-label>
          <q-item-label caption>{{ p.description || p.category || '-' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
    <q-card v-else flat bordered>No products. Add via Scan.</q-card>

    <q-dialog v-model="detailDialog">
      <q-card v-if="selectedProduct" style="min-width: 320px">
        <q-card-section>
          <div class="text-h6">{{ selectedProduct.name }}</div>
          <div class="text-caption">ID: {{ selectedProduct.id }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import { getMeProducts } from '../services/api'

const deviceStore = useDeviceStore()
const search = ref('')
const products = ref([])
const loading = ref(false)
const detailDialog = ref(false)
const selectedProduct = ref(null)

onMounted(() => loadProducts())

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
</script>
