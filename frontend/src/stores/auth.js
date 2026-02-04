import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const username = ref('')
  const authEnabled = ref(true)

  const isAuthenticated = computed(() => !!username.value)

  function setUser(name) {
    username.value = name
  }

  function clearUser() {
    username.value = ''
  }

  return { username, authEnabled, isAuthenticated, setUser, clearUser }
})
