import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDeviceFingerprint } from '../services/device'

export const useDeviceStore = defineStore('device', () => {
  const fingerprint = ref('')
  const deviceName = ref('')
  const defaultAction = ref('add')

  async function ensureFingerprint() {
    if (!fingerprint.value) {
      fingerprint.value = await getDeviceFingerprint()
    }
    return fingerprint.value
  }

  function setDevice(name, action) {
    if (name != null) deviceName.value = name
    if (action != null) defaultAction.value = action
  }

  return { fingerprint, deviceName, defaultAction, ensureFingerprint, setDevice }
})
