<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated data-testid="app-header">
      <q-toolbar>
        <q-btn flat dense round icon="menu" class="lt-md" @click="drawer = !drawer" data-testid="mobile-menu-button" />
        <q-toolbar-title data-testid="app-logo">{{ configStore.appTitle }}</q-toolbar-title>
        <!-- Desktop nav -->
        <q-btn flat label="Scan" to="/scan" class="gt-sm" data-testid="nav-scan" />
        <q-btn flat label="Products" to="/products" class="gt-sm" data-testid="nav-products" />
        <q-btn flat label="Inventory" to="/inventory" class="gt-sm" data-testid="nav-inventory" />
        <q-btn flat label="Locations" to="/locations" class="gt-sm" data-testid="nav-locations" />
        <q-btn flat label="Jobs" to="/jobs" class="gt-sm" data-testid="nav-jobs" />
        <q-btn flat label="Logs" to="/logs" class="gt-sm" data-testid="nav-logs" />
        <q-btn flat label="Settings" to="/settings" class="gt-sm" data-testid="nav-settings" />
        <q-btn v-if="authStore.isAuthenticated" flat icon="logout" @click="logout" data-testid="logout-button" />
      </q-toolbar>
    </q-header>

    <!-- Mobile drawer -->
    <q-drawer v-model="drawer" side="left" bordered class="lt-md" data-testid="mobile-drawer">
      <q-list>
        <q-item clickable v-close-popup to="/scan" data-testid="mobile-nav-scan">
          <q-item-section avatar><q-icon name="qr_code_scanner" /></q-item-section>
          <q-item-section>Scan</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/products" data-testid="mobile-nav-products">
          <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
          <q-item-section>Products</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/inventory" data-testid="mobile-nav-inventory">
          <q-item-section avatar><q-icon name="list_alt" /></q-item-section>
          <q-item-section>Inventory</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/locations" data-testid="mobile-nav-locations">
          <q-item-section avatar><q-icon name="location_on" /></q-item-section>
          <q-item-section>Locations</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/jobs" data-testid="mobile-nav-jobs">
          <q-item-section avatar><q-icon name="work" /></q-item-section>
          <q-item-section>Jobs</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/logs" data-testid="mobile-nav-logs">
          <q-item-section avatar><q-icon name="article" /></q-item-section>
          <q-item-section>Logs</q-item-section>
        </q-item>
        <q-item clickable v-close-popup to="/settings" data-testid="mobile-nav-settings">
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
