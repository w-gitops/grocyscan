<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>GrocyScan</q-toolbar-title>
        <q-btn flat label="Scan" to="/scan" />
        <q-btn flat label="Products" to="/products" />
        <q-btn v-if="authStore.isAuthenticated" flat icon="logout" @click="logout" />
      </q-toolbar>
    </q-header>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { apiFetch } from '../services/api'

const authStore = useAuthStore()
const router = useRouter()

async function logout() {
  try {
    await apiFetch('/api/auth/logout', { method: 'POST' })
  } finally {
    authStore.clearUser()
    router.replace('/login')
  }
}
</script>
