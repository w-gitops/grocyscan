<template>
  <q-page class="logs-page q-pa-md">
    <!-- Page header -->
    <div class="row items-center q-mb-md">
      <div class="text-h5">Logs</div>
      <q-space />
      <q-btn flat round icon="refresh" @click="loadLogs" :loading="loading" />
    </div>

    <q-banner v-if="message" class="bg-warning text-white q-mb-md rounded-borders">
      {{ message }}
    </q-banner>

    <!-- Toolbar -->
    <q-card flat bordered class="logs-toolbar q-mb-md">
      <q-card-section class="q-py-sm q-px-md row items-center flex-wrap">
        <div class="row items-center q-gutter-xs flex-wrap">
          <span class="text-caption text-weight-medium">Level:</span>
          <q-btn
            v-for="lvl in levelOptions"
            :key="lvl.value"
            :label="lvl.label"
            :color="levelFilter === lvl.value ? levelChipColor(lvl.value) : 'grey-7'"
            :outline="levelFilter !== lvl.value"
            size="sm"
            dense
            no-caps
            @click="levelFilter = lvl.value"
          />
        </div>
        <q-separator vertical class="q-mx-sm" />
        <q-input
          v-model="searchQuery"
          dense
          outlined
          placeholder="Search..."
          clearable
          class="log-search-input"
          style="min-width: 140px; max-width: 200px"
        >
          <template #prepend>
            <q-icon name="search" size="xs" />
          </template>
        </q-input>
        <q-separator vertical class="q-mx-sm" />
        <q-btn
          :icon="tailing ? 'pause' : 'play_arrow'"
          :label="tailing ? 'Pause' : 'Follow'"
          :color="tailing ? 'primary' : 'grey-7'"
          :outline="!tailing"
          size="sm"
          dense
          no-caps
          @click="tailing = !tailing"
        />
        <q-btn
          :icon="orderNewestFirst ? 'arrow_upward' : 'arrow_downward'"
          :label="orderNewestFirst ? 'Newest' : 'Oldest'"
          outline
          size="sm"
          dense
          no-caps
          class="q-ml-xs"
          @click="orderNewestFirst = !orderNewestFirst"
        />
        <q-space />
        <q-btn flat round dense icon="file_download" @click="downloadLogs" :disable="!displayedLines.length">
          <q-tooltip>Download</q-tooltip>
        </q-btn>
        <q-btn flat round dense icon="content_copy" @click="copyLogs" :disable="!displayedLines.length">
          <q-tooltip>Copy</q-tooltip>
        </q-btn>
        <q-btn flat round dense icon="delete" color="negative" @click="confirmClear" :disable="!rawLines.length">
          <q-tooltip>Clear log file</q-tooltip>
        </q-btn>
      </q-card-section>
    </q-card>

    <!-- Log viewer panel -->
    <q-card flat bordered class="log-viewer-card">
      <div class="log-viewer-header row items-center">
        <span class="text-caption">{{ logFilePath || 'Application logs' }}</span>
        <q-space />
        <span class="text-caption">{{ displayedLines.length }} line(s)</span>
      </div>
      <div v-if="loading && !rawLines.length" class="log-viewer-body log-viewer-body--empty">
        <q-spinner size="md" color="grey-5" />
        <span class="q-mt-sm">Loading...</span>
      </div>
      <div v-else-if="!rawLines.length" class="log-viewer-body log-viewer-body--empty">
        <span class="text-weight-medium">No log entries.</span>
        <p v-if="message" class="log-viewer-empty-hint">{{ message }}</p>
        <p v-else class="log-viewer-empty-hint">Set LOG_FILE on the server (e.g. /opt/grocyscan/logs/app.log) and restart the service to capture logs here.</p>
      </div>
      <div v-else-if="!displayedLines.length" class="log-viewer-body log-viewer-body--empty">
        <span class="text-weight-medium">No lines match the current filters.</span>
        <p class="log-viewer-empty-hint">Try "All" levels or clear the search.</p>
      </div>
      <div
        v-else
        ref="logScrollRef"
        class="log-viewer-body"
        @scroll="onScroll"
      >
        <div
          v-for="(entry, idx) in displayedLines"
          :key="entry.id"
          class="log-row"
          :class="{ 'log-row--match': searchQuery && entry.rawLower.includes(searchQueryLower) }"
        >
          <span v-if="entry.timestamp" class="log-ts">{{ entry.timestamp }}</span>
          <span :class="['log-badge', 'log-badge--' + (entry.level || 'info')]">
            {{ (entry.level || 'info').toUpperCase() }}
          </span>
          <span class="log-msg" v-html="entry.messageHtml" />
        </div>
      </div>
      <q-btn
        v-if="!tailing && rawLines.length && !atBottom"
        flat
        round
        dense
        icon="keyboard_arrow_down"
        class="scroll-to-bottom-btn"
        @click="scrollToBottom"
      >
        <q-tooltip>Scroll to bottom</q-tooltip>
      </q-btn>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { getLogs, clearLogs } from '../services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const rawLines = ref([])
const message = ref('')
const logFilePath = ref(null)
const loading = ref(false)
const logScrollRef = ref(null)
const atBottom = ref(true)
const tailing = ref(false)
const levelFilter = ref('all')
const searchQuery = ref('')
const orderNewestFirst = ref(false)

const TAIL_INTERVAL_MS = 3000
let tailIntervalId = null

const levelRegex = /\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]|"level"\s*:\s*"(debug|info|warning|error|critical)"/i
const levelBracketRe = /\[\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]\s*/i
const timestampRe = /^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s*/

const levelOptions = [
  { value: 'all', label: 'All' },
  { value: 'debug', label: 'DEBUG' },
  { value: 'info', label: 'INFO' },
  { value: 'warning', label: 'WARNING' },
  { value: 'error', label: 'ERROR' },
  { value: 'critical', label: 'CRITICAL' },
]

function detectLevel(line) {
  const m = levelRegex.exec(line)
  if (m) return (m[1] || m[2] || '').toLowerCase()
  return 'info'
}

function stripLevelBracket(line) {
  return line.replace(levelBracketRe, '').trim()
}

function splitTimestamp(line) {
  const m = timestampRe.match(line)
  if (m) return { timestamp: m[1], rest: line.slice(m[0].length).trim() }
  return { timestamp: '', rest: line }
}

function escapeHtml(s) {
  if (!s) return ''
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function highlightSearch(text, query) {
  if (!query || !query.trim()) return escapeHtml(text)
  const escaped = escapeHtml(text)
  const lower = query.trim().toLowerCase()
  const idx = escaped.toLowerCase().indexOf(lower)
  if (idx === -1) return escaped
  const before = escaped.slice(0, idx)
  const match = escaped.slice(idx, idx + query.trim().length)
  const after = escaped.slice(idx + query.trim().length)
  return `${before}<mark class="log-highlight">${match}</mark>${after}`
}

function levelChipColor(level) {
  const colors = { all: 'grey', debug: 'grey', info: 'blue', warning: 'orange', error: 'red', critical: 'red' }
  return colors[level] || 'grey'
}

function parseLine(raw, index) {
  const level = detectLevel(raw)
  const stripped = stripLevelBracket(raw)
  const { timestamp, rest } = splitTimestamp(stripped)
  const message = rest || stripped || raw
  return {
    id: `log-${index}-${raw.slice(0, 40)}`,
    raw,
    rawLower: raw.toLowerCase(),
    level,
    timestamp,
    message,
  }
}

const searchQueryLower = computed(() => (searchQuery.value || '').trim().toLowerCase())

const parsedLines = computed(() =>
  rawLines.value.map((line, i) => parseLine(line, i))
)

const displayedLines = computed(() => {
  let list = parsedLines.value

  if (levelFilter.value && levelFilter.value !== 'all') {
    list = list.filter((e) => e.level === levelFilter.value)
  }
  if (searchQueryLower.value) {
    list = list.filter((e) => e.rawLower.includes(searchQueryLower.value))
  }
  if (orderNewestFirst.value) {
    list = [...list].reverse()
  }
  return list.map((e) => ({
    ...e,
    messageHtml: highlightSearch(e.message, searchQuery.value),
  }))
})

function onScroll() {
  if (!logScrollRef.value) return
  const el = logScrollRef.value
  const threshold = 80
  atBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < threshold
}

function scrollToBottom() {
  nextTick(() => {
    if (logScrollRef.value) {
      logScrollRef.value.scrollTop = logScrollRef.value.scrollHeight
      atBottom.value = true
    }
  })
}

async function loadLogs() {
  loading.value = true
  try {
    const data = await getLogs()
    rawLines.value = data.lines || []
    message.value = data.message || ''
    logFilePath.value = data.log_file || null
  } catch (e) {
    $q.notify({ type: 'negative', message: e.message || 'Failed to load logs' })
  } finally {
    loading.value = false
  }
  if (tailing.value) nextTick(scrollToBottom)
}

watch(tailing, (on) => {
  if (on) {
    tailIntervalId = setInterval(loadLogs, TAIL_INTERVAL_MS)
    nextTick(scrollToBottom)
  } else {
    if (tailIntervalId) clearInterval(tailIntervalId)
    tailIntervalId = null
  }
})

function downloadLogs() {
  if (!displayedLines.value.length) return
  const text = displayedLines.value.map((e) => e.raw).join('\n')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `grocyscan-logs-${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
  $q.notify({ type: 'positive', message: 'Logs downloaded' })
}

function copyLogs() {
  if (!displayedLines.value.length) {
    $q.notify({ type: 'warning', message: 'Nothing to copy' })
    return
  }
  const text = displayedLines.value.map((e) => e.raw).join('\n')
  navigator.clipboard.writeText(text).then(
    () => $q.notify({ type: 'positive', message: 'Copied to clipboard' }),
    () => $q.notify({ type: 'negative', message: 'Copy failed' })
  )
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
      rawLines.value = []
      message.value = ''
      $q.notify({ type: 'positive', message: 'Logs cleared' })
    } catch (e) {
      $q.notify({ type: 'negative', message: e.message || 'Failed to clear logs' })
    }
  })
}

onMounted(loadLogs)
onUnmounted(() => {
  if (tailIntervalId) clearInterval(tailIntervalId)
})
</script>

<style scoped>
.logs-page {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.logs-toolbar .q-card__section {
  gap: 4px;
}

.log-viewer-card {
  position: relative;
  flex: 1 1 auto;
  min-height: 380px;
  max-height: calc(100vh - 260px);
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.log-viewer-header {
  flex-shrink: 0;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.75rem;
  color: #94a3b8;
}

.log-viewer-body {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #e2e8f0;
}

.log-viewer-body--empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  text-align: center;
  padding: 24px;
}

.log-viewer-empty-hint {
  margin: 8px 0 0;
  font-size: 0.8rem;
  color: #64748b;
  max-width: 420px;
  line-height: 1.4;
}

.log-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 3px 0;
  white-space: pre-wrap;
  word-break: break-word;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.log-row--match {
  background: rgba(59, 130, 246, 0.12);
}

.log-ts {
  color: #64748b;
  flex-shrink: 0;
  font-size: 0.75rem;
}

.log-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  min-width: 4.25rem;
  text-align: center;
}

.log-badge--debug {
  background: #475569;
  color: #e2e8f0;
}

.log-badge--info {
  background: #16a34a;
  color: white;
}

.log-badge--warning {
  background: #ca8a04;
  color: #1e293b;
}

.log-badge--error {
  background: #dc2626;
  color: white;
}

.log-badge--critical {
  background: #7f1d1d;
  color: #fecaca;
}

.log-msg {
  flex: 1;
  min-width: 0;
}

.log-msg :deep(.log-highlight) {
  background: rgba(250, 204, 21, 0.45);
  color: #fef08a;
  padding: 0 2px;
  border-radius: 2px;
}

.scroll-to-bottom-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  background: rgba(15, 23, 42, 0.95);
  color: #94a3b8;
}

.scroll-to-bottom-btn:hover {
  background: rgba(30, 41, 59, 0.98);
  color: #e2e8f0;
}
</style>
