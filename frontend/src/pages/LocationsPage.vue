<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Locations</div>

    <q-card v-if="loading" flat bordered class="q-mb-md">
      <q-card-section>Loading...</q-card-section>
    </q-card>

    <q-list v-else-if="locations.length" bordered separator>
      <q-item v-for="loc in locations" :key="loc.id">
        <q-item-section avatar>
          <q-icon :name="loc.is_freezer ? 'ac_unit' : 'location_on'" :color="loc.is_freezer ? 'blue' : 'grey'" />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ loc.name }}</q-item-label>
          <q-item-label caption>{{ loc.location_type }}{{ loc.description ? ' - ' + loc.description : '' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <q-card v-else flat bordered>
      <q-card-section>No locations configured. Add locations via Settings or API.</q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import { getMeLocations } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()
const locations = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    locations.value = await getMeLocations(fp)
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load locations' })
  } finally {
    loading.value = false
  }
})
</script>
