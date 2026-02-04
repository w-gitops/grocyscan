<template>
  <q-page class="q-pa-md">
    <div class="text-h5 q-mb-md">Job Queue</div>

    <!-- Stats cards -->
    <div class="row q-gutter-sm q-mb-md">
      <q-card class="col-6 col-md-3">
        <q-card-section>
          <div class="text-caption text-grey">Pending</div>
          <div class="text-h6">{{ stats.pending || 0 }}</div>
        </q-card-section>
      </q-card>
      <q-card class="col-6 col-md-3">
        <q-card-section>
          <div class="text-caption text-grey">Running</div>
          <div class="text-h6 text-blue">{{ stats.running || 0 }}</div>
        </q-card-section>
      </q-card>
      <q-card class="col-6 col-md-3">
        <q-card-section>
          <div class="text-caption text-grey">Completed</div>
          <div class="text-h6 text-green">{{ stats.completed || 0 }}</div>
        </q-card-section>
      </q-card>
      <q-card class="col-6 col-md-3">
        <q-card-section>
          <div class="text-caption text-grey">Failed</div>
          <div class="text-h6 text-red">{{ stats.failed || 0 }}</div>
        </q-card-section>
      </q-card>
    </div>

    <!-- Filter -->
    <q-select
      v-model="statusFilter"
      :options="['All', 'pending', 'running', 'completed', 'failed', 'cancelled']"
      label="Filter by status"
      dense
      outlined
      class="q-mb-md"
      style="max-width: 200px"
      @update:model-value="loadJobs"
    />

    <!-- Jobs list -->
    <q-card v-if="loading" flat bordered>
      <q-card-section>Loading...</q-card-section>
    </q-card>

    <q-list v-else-if="jobs.length" bordered separator>
      <q-item v-for="job in jobs" :key="job.id">
        <q-item-section>
          <q-item-label>{{ job.job_type }}</q-item-label>
          <q-item-label caption>{{ job.id }} - {{ job.status }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-badge :color="statusColor(job.status)">{{ job.status }}</q-badge>
        </q-item-section>
      </q-item>
    </q-list>

    <q-card v-else flat bordered>
      <q-card-section>No jobs in queue.</q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getJobs } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const jobs = ref([])
const stats = ref({})
const loading = ref(false)
const statusFilter = ref('All')

function statusColor(status) {
  const colors = {
    pending: 'grey',
    running: 'blue',
    completed: 'green',
    failed: 'red',
    cancelled: 'orange',
  }
  return colors[status] || 'grey'
}

async function loadJobs() {
  loading.value = true
  try {
    const filter = statusFilter.value === 'All' ? null : statusFilter.value
    const data = await getJobs(filter)
    jobs.value = data.jobs || []
    stats.value = data.stats || {}
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load jobs' })
  } finally {
    loading.value = false
  }
}

onMounted(loadJobs)
</script>
