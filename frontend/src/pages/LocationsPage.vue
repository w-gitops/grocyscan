<template>
  <q-page class="q-pa-md" data-testid="locations-page">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Locations</div>
      <q-space />
      <q-btn icon="add" label="Add Location" color="primary" @click="addDialog = true" data-testid="locations-add-button" />
    </div>

    <q-card v-if="loading" flat bordered class="q-mb-md" data-testid="locations-loading">
      <q-card-section>Loading...</q-card-section>
    </q-card>

    <q-list v-else-if="locations.length" bordered separator data-testid="locations-list">
      <q-item v-for="loc in locations" :key="loc.id" data-testid="location-card">
        <q-item-section avatar>
          <q-icon :name="loc.is_freezer ? 'ac_unit' : 'location_on'" :color="loc.is_freezer ? 'blue' : 'grey'" :data-testid="loc.is_freezer ? 'location-freezer-icon' : 'location-icon'" />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ loc.name }}</q-item-label>
          <q-item-label caption>{{ loc.location_type }}{{ loc.description ? ' - ' + loc.description : '' }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <q-card v-else flat bordered data-testid="locations-empty">
      <q-card-section>No locations configured. Click "Add Location" to create one.</q-card-section>
    </q-card>

    <!-- Add Location dialog -->
    <q-dialog v-model="addDialog" data-testid="location-dialog">
      <q-card style="min-width: 320px" data-testid="location-dialog-card">
        <q-card-section>
          <div class="text-h6">Add Location</div>
        </q-card-section>
        <q-card-section>
          <q-input v-model="newLoc.name" label="Name" outlined dense class="q-mb-sm" data-testid="location-name-input" />
          <q-input v-model="newLoc.description" label="Description (optional)" outlined dense class="q-mb-sm" data-testid="location-description-input" />
          <q-select
            v-model="newLoc.location_type"
            :options="['shelf', 'fridge', 'freezer', 'pantry', 'cabinet', 'other']"
            label="Type"
            outlined
            dense
            class="q-mb-sm"
            data-testid="location-type-select"
          />
          <q-toggle v-model="newLoc.is_freezer" label="Is freezer" data-testid="location-freezer-toggle" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup data-testid="location-cancel-button" />
          <q-btn flat label="Add" color="primary" @click="createLocation" :loading="saving" data-testid="location-save-button" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import { getMeLocations, createMeLocation } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()
const locations = ref([])
const loading = ref(false)
const addDialog = ref(false)
const saving = ref(false)
const newLoc = ref({ name: '', description: '', location_type: 'shelf', is_freezer: false })

async function loadLocations() {
  loading.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    locations.value = await getMeLocations(fp)
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load locations' })
  } finally {
    loading.value = false
  }
}

async function createLocation() {
  if (!newLoc.value.name.trim()) {
    $q.notify({ type: 'warning', message: 'Name is required' })
    return
  }
  saving.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    await createMeLocation(fp, newLoc.value)
    addDialog.value = false
    newLoc.value = { name: '', description: '', location_type: 'shelf', is_freezer: false }
    $q.notify({ type: 'positive', message: 'Location added' })
    await loadLocations()
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to create location' })
  } finally {
    saving.value = false
  }
}

onMounted(loadLocations)
</script>
