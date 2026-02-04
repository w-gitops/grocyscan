<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Logs</div>
      <q-space />
      <q-btn flat icon="refresh" @click="loadLogs" :loading="loading" />
      <q-btn flat icon="delete" color="negative" @click="confirmClear" :disable="!lines.length" />
    </div>

    <q-banner v-if="message" class="bg-warning text-white q-mb-md rounded-borders">
      {{ message }}
    </q-banner>

    <q-card flat bordered>
      <q-card-section v-if="loading">Loading...</q-card-section>
      <q-card-section v-else-if="!lines.length" class="text-grey">
        No log entries.
      </q-card-section>
      <q-virtual-scroll v-else :items="lines" style="max-height: 60vh" v-slot="{ item }">
        <div class="log-line q-pa-xs" style="font-family: monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;">
          <q-badge v-if="detectLevel(item)" :color="levelColor(detectLevel(item))" class="q-mr-xs">
            {{ detectLevel(item).toUpperCase() }}
          </q-badge>
          {{ stripLevel(item) }}
        </div>
      </q-virtual-scroll>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs, clearLogs } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const lines = ref([])
const message = ref('')
const loading = ref(false)

const levelRegex = /\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]|"level"\s*:\s*"(debug|info|warning|error|critical)"/i

function detectLevel(line) {
  const m = levelRegex.exec(line)
  if (m) return (m[1] || m[2] || '').toLowerCase()
  return ''
}

function stripLevel(line) {
  return line.replace(/\[\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]\s*/i, '').trim()
}

function levelColor(level) {
  const colors = { debug: 'grey', info: 'blue', warning: 'orange', error: 'red', critical: 'red' }
  return colors[level] || 'grey'
}

async function loadLogs() {
  loading.value = true
  try {
    const data = await getLogs()
    lines.value = data.lines || []
    message.value = data.message || ''
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load logs' })
  } finally {
    loading.value = false
  }
}

function confirmClear() {
  $q.dialog({
    title: 'Clear Logs',
    message: 'Are you sure you want to clear the log file?',
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await clearLogs()
      lines.value = []
      $q.notify({ type: 'positive', message: 'Logs cleared' })
    } catch (e) {
      $q.notify({ type: 'negative', message: e.message || 'Failed to clear logs' })
    }
  })
}

onMounted(loadLogs)
</script>
