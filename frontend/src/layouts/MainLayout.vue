<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" class="lt-md" @click="drawer = !drawer" />
        <q-toolbar-title>{{ configStore.appTitle }}</q-toolbar-title>
        <!-- Desktop nav -->
        <q-btn flat label="Scan" to="/scan" class="gt-sm" />
        <q-btn flat label="Products" to="/products" class="gt-sm" />
        <q-btn flat label="Locations" to="/locations" class="gt-sm" />
        <q-btn flat label="Jobs" to="/jobs" class="gt-sm" />
        <q-btn flat label="Logs" to="/logs" class="gt-sm" />
        <q-btn flat label="Settings" to="/settings" class="gt-sm" />
        <q-btn v-if="authStore.isAuthenticated" flat icon="logout" @click="logout" />
      </q-toolbar>
    </q-header>

    <!-- Mobile drawer -->
    <q-drawer v-model="drawer" side="left" bordered class="lt-md">
      <q-list>
        <q-item clickable v-close-popup to="/scan">
          <q-item-section avatar><q-icon name="qr_code_scanner" /></q-item-section>
          <q-item-section>Scan</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/products">
          <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
          <q-item-section>Products</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/locations">
          <q-item-section avatar><q-icon name="location_on" /></q-item-section>
          <q-item-section>Locations</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/jobs">
          <q-item-section avatar><q-icon name="work" /></q-item-section>
          <q-item-section>Jobs</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/logs">
          <q-item-section avatar><q-icon name="article" /></q-item-section>
          <q-item-section>Logs</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/settings">
          <q-item-section avatar><q-icon name="settings" /></q-item-section>
          <q-item-section>Settings</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useConfigStore } from '../stores/config'
import { useRouter } from 'vue-router'
import { apiFetch } from '../services/api'

const authStore = useAuthStore()
const configStore = useConfigStore()
const router = useRouter()
const drawer = ref(false)

async function logout() {
  try {
    await apiFetch('/api/auth/logout', { method: 'POST' })
  } finally {
    authStore.clearUser()
    router.replace('/login')
  }
}
</script>
