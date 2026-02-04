<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Locations</div>
      <q-space />
      <q-btn
        icon="add"
        label="Add Location"
        color="primary"
        @click="openAddDialog()"
        data-testid="location-add-btn"
      />
    </div>

    <q-card v-if="loading" flat bordered class="q-mb-md">
      <q-card-section>Loading...</q-card-section>
    </q-card>

    <!-- Location tree/list -->
    <q-list v-else-if="locationTree.length" bordered separator data-testid="location-tree">
      <template v-for="loc in locationTree" :key="loc.id">
        <q-item :style="{ paddingLeft: '0px' }" :data-testid="`location-row-${loc.id}`">
          <q-item-section avatar>
            <q-icon :name="loc.is_freezer ? 'ac_unit' : 'location_on'" :color="loc.is_freezer ? 'blue' : 'grey'" />
          </q-item-section>
          <q-item-section>
            <q-item-label>
              {{ loc.name }}
              <q-badge v-if="loc.is_freezer" class="q-ml-sm" color="blue" label="Freezer" />
            </q-item-label>
            <q-item-label caption>{{ loc.location_type }}{{ loc.description ? ' - ' + loc.description : '' }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="row no-wrap">
              <q-btn flat round dense icon="keyboard_arrow_up" @click="moveLocation(loc, -1)" data-testid="location-move-up-btn" />
              <q-btn flat round dense icon="keyboard_arrow_down" @click="moveLocation(loc, 1)" data-testid="location-move-down-btn" />
              <q-btn flat round dense icon="add" @click="openAddDialog(loc)" data-testid="location-add-child-btn" />
              <q-btn flat round dense icon="edit" @click="openEditDialog(loc)" data-testid="location-edit-btn" />
              <q-btn flat round dense icon="delete" color="negative" @click="confirmDelete(loc)" data-testid="location-delete-btn" />
            </div>
          </q-item-section>
        </q-item>
        <!-- Render children recursively -->
        <template v-for="child in loc.children" :key="child.id">
          <q-item :style="{ paddingLeft: '24px' }" :data-testid="`location-row-${child.id}`">
            <q-item-section avatar>
              <q-icon :name="child.is_freezer ? 'ac_unit' : 'location_on'" :color="child.is_freezer ? 'blue' : 'grey'" />
            </q-item-section>
            <q-item-section>
              <q-item-label>
                {{ child.name }}
                <q-badge v-if="child.is_freezer" class="q-ml-sm" color="blue" label="Freezer" />
              </q-item-label>
              <q-item-label caption>{{ child.location_type }}{{ child.description ? ' - ' + child.description : '' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div class="row no-wrap">
                <q-btn flat round dense icon="keyboard_arrow_up" @click="moveLocation(child, -1)" data-testid="location-move-up-btn" />
                <q-btn flat round dense icon="keyboard_arrow_down" @click="moveLocation(child, 1)" data-testid="location-move-down-btn" />
                <q-btn flat round dense icon="add" @click="openAddDialog(child)" data-testid="location-add-child-btn" />
                <q-btn flat round dense icon="edit" @click="openEditDialog(child)" data-testid="location-edit-btn" />
                <q-btn flat round dense icon="delete" color="negative" @click="confirmDelete(child)" data-testid="location-delete-btn" />
              </div>
            </q-item-section>
          </q-item>
          <!-- Level 3 children -->
          <template v-for="grandchild in child.children" :key="grandchild.id">
            <q-item :style="{ paddingLeft: '48px' }" :data-testid="`location-row-${grandchild.id}`">
              <q-item-section avatar>
                <q-icon :name="grandchild.is_freezer ? 'ac_unit' : 'location_on'" :color="grandchild.is_freezer ? 'blue' : 'grey'" />
              </q-item-section>
              <q-item-section>
                <q-item-label>
                  {{ grandchild.name }}
                  <q-badge v-if="grandchild.is_freezer" class="q-ml-sm" color="blue" label="Freezer" />
                </q-item-label>
                <q-item-label caption>{{ grandchild.location_type }}{{ grandchild.description ? ' - ' + grandchild.description : '' }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="row no-wrap">
                  <q-btn flat round dense icon="keyboard_arrow_up" @click="moveLocation(grandchild, -1)" />
                  <q-btn flat round dense icon="keyboard_arrow_down" @click="moveLocation(grandchild, 1)" />
                  <q-btn flat round dense icon="add" @click="openAddDialog(grandchild)" />
                  <q-btn flat round dense icon="edit" @click="openEditDialog(grandchild)" />
                  <q-btn flat round dense icon="delete" color="negative" @click="confirmDelete(grandchild)" />
                </div>
              </q-item-section>
            </q-item>
          </template>
        </template>
      </template>
    </q-list>

    <q-card v-else flat bordered>
      <q-card-section>No locations configured. Click "Add Location" to create one.</q-card-section>
    </q-card>

    <!-- Add/Edit Location dialog -->
    <q-dialog v-model="editDialog" data-testid="location-edit-dialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">{{ editingLocation ? 'Edit Location' : 'Add Location' }}</div>
        </q-card-section>
        <q-card-section>
          <q-input
            v-model="formData.name"
            label="Name"
            outlined
            dense
            class="q-mb-sm"
            data-testid="location-name-input"
          />
          <q-input
            v-model="formData.description"
            label="Description (optional)"
            outlined
            dense
            class="q-mb-sm"
          />
          <q-select
            v-model="formData.location_type"
            :options="locationTypes"
            label="Type"
            outlined
            dense
            class="q-mb-sm"
          />
          <q-select
            v-model="formData.parent_id"
            :options="parentOptions"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            label="Parent Location"
            outlined
            dense
            clearable
            class="q-mb-sm"
            data-testid="location-parent-select"
          />
          <q-toggle
            v-model="formData.is_freezer"
            label="Is freezer"
            data-testid="location-freezer-toggle"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            :label="editingLocation ? 'Save' : 'Add'"
            color="primary"
            @click="saveLocation"
            :loading="saving"
            data-testid="location-save-btn"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete confirmation dialog -->
    <q-dialog v-model="deleteDialog">
      <q-card>
        <q-card-section>
          <div class="text-h6">Delete Location</div>
        </q-card-section>
        <q-card-section>
          Are you sure you want to delete "{{ deletingLocation?.name }}"?
          <div v-if="deleteWarning" class="text-negative q-mt-sm">{{ deleteWarning }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Delete"
            color="negative"
            @click="deleteLocation"
            :loading="deleting"
            data-testid="location-delete-confirm"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device'
import { getMeLocations, createMeLocation, updateMeLocation, deleteMeLocation } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const deviceStore = useDeviceStore()
const locations = ref([])
const loading = ref(false)
const editDialog = ref(false)
const deleteDialog = ref(false)
const saving = ref(false)
const deleting = ref(false)
const editingLocation = ref(null)
const deletingLocation = ref(null)
const deleteWarning = ref('')

const locationTypes = ['room', 'shelf', 'fridge', 'freezer', 'pantry', 'cabinet', 'drawer', 'other']

const formData = ref({
  name: '',
  description: '',
  location_type: 'shelf',
  parent_id: null,
  is_freezer: false,
  sort_order: 0,
})

// Build location tree from flat list
const locationTree = computed(() => {
  const map = new Map()
  const roots = []

  // Create map of all locations
  for (const loc of locations.value) {
    map.set(loc.id, { ...loc, children: [] })
  }

  // Build tree
  for (const loc of locations.value) {
    const node = map.get(loc.id)
    if (loc.parent_id && map.has(loc.parent_id)) {
      map.get(loc.parent_id).children.push(node)
    } else {
      roots.push(node)
    }
  }

  // Sort by sort_order, then name
  const sortFn = (a, b) => (a.sort_order - b.sort_order) || a.name.localeCompare(b.name)
  const sortTree = (nodes) => {
    nodes.sort(sortFn)
    for (const node of nodes) {
      sortTree(node.children)
    }
  }
  sortTree(roots)

  return roots
})

// Parent options for dropdown (exclude self and descendants when editing)
const parentOptions = computed(() => {
  const options = [{ label: '(None - Top Level)', value: null }]

  const addOptions = (nodes, prefix = '') => {
    for (const node of nodes) {
      // When editing, exclude self and descendants
      if (editingLocation.value && isDescendant(editingLocation.value.id, node.id)) {
        continue
      }
      options.push({ label: prefix + node.name, value: node.id })
      if (node.children?.length) {
        addOptions(node.children, prefix + '  ')
      }
    }
  }
  addOptions(locationTree.value)
  return options
})

function isDescendant(ancestorId, nodeId) {
  // Check if nodeId is ancestorId or a descendant of it
  if (ancestorId === nodeId) return true
  const findInTree = (nodes, id) => {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const found = findInTree(n.children, id)
        if (found) return found
      }
    }
    return null
  }
  const ancestor = findInTree(locationTree.value, ancestorId)
  if (!ancestor) return false
  const findDesc = (node, targetId) => {
    if (node.id === targetId) return true
    return node.children?.some(c => findDesc(c, targetId)) || false
  }
  return findDesc(ancestor, nodeId)
}

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

function openAddDialog(parentLocation = null) {
  editingLocation.value = null
  formData.value = {
    name: '',
    description: '',
    location_type: 'shelf',
    parent_id: parentLocation?.id || null,
    is_freezer: false,
    sort_order: 0,
  }
  editDialog.value = true
}

function openEditDialog(loc) {
  editingLocation.value = loc
  formData.value = {
    name: loc.name,
    description: loc.description || '',
    location_type: loc.location_type,
    parent_id: loc.parent_id,
    is_freezer: loc.is_freezer,
    sort_order: loc.sort_order,
  }
  editDialog.value = true
}

async function saveLocation() {
  if (!formData.value.name.trim()) {
    $q.notify({ type: 'warning', message: 'Name is required' })
    return
  }
  saving.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    if (editingLocation.value) {
      await updateMeLocation(fp, editingLocation.value.id, formData.value)
      $q.notify({ type: 'positive', message: 'Location updated' })
    } else {
      await createMeLocation(fp, formData.value)
      $q.notify({ type: 'positive', message: 'Location added' })
    }
    editDialog.value = false
    await loadLocations()
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to save location' })
  } finally {
    saving.value = false
  }
}

function confirmDelete(loc) {
  deletingLocation.value = loc
  deleteWarning.value = ''
  // Check for children in the tree
  const findNode = (nodes, id) => {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const found = findNode(n.children, id)
        if (found) return found
      }
    }
    return null
  }
  const node = findNode(locationTree.value, loc.id)
  if (node?.children?.length) {
    deleteWarning.value = 'This location has children. Move or delete them first.'
  }
  deleteDialog.value = true
}

async function deleteLocation() {
  if (!deletingLocation.value) return
  deleting.value = true
  try {
    const fp = await deviceStore.ensureFingerprint()
    await deleteMeLocation(fp, deletingLocation.value.id)
    $q.notify({ type: 'positive', message: 'Location deleted' })
    deleteDialog.value = false
    await loadLocations()
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to delete location' })
  } finally {
    deleting.value = false
  }
}

async function moveLocation(loc, direction) {
  // Get siblings
  const siblings = loc.parent_id
    ? locations.value.filter(l => l.parent_id === loc.parent_id)
    : locations.value.filter(l => !l.parent_id)
  siblings.sort((a, b) => (a.sort_order - b.sort_order) || a.name.localeCompare(b.name))

  const idx = siblings.findIndex(s => s.id === loc.id)
  const targetIdx = idx + direction
  if (targetIdx < 0 || targetIdx >= siblings.length) return

  // Swap sort orders
  const target = siblings[targetIdx]
  const tempOrder = target.sort_order
  const newTargetOrder = loc.sort_order
  const newLocOrder = tempOrder

  try {
    const fp = await deviceStore.ensureFingerprint()
    await Promise.all([
      updateMeLocation(fp, loc.id, { sort_order: newLocOrder }),
      updateMeLocation(fp, target.id, { sort_order: newTargetOrder }),
    ])
    await loadLocations()
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to reorder' })
  }
}

onMounted(loadLocations)
</script>

<style scoped>
</style>
