/**
 * App config from backend (e.g. product title).
 * Fetches once; falls back to default until loaded.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

const DEFAULT_APP_TITLE = 'HomeBot'

export const useConfigStore = defineStore('config', () => {
  const appTitle = ref(DEFAULT_APP_TITLE)
  const version = ref('')
  let loaded = false

  async function load() {
    if (loaded) return
    try {
      const res = await apiFetch('/api/config')
      if (res.ok) {
        const data = await res.json()
        if (data.app_title) appTitle.value = data.app_title
        if (data.version) version.value = data.version
      }
    } catch {
      // keep default
    } finally {
      loaded = true
    }
  }

  return { appTitle, version, load }
})
