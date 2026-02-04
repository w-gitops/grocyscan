<template>
  <div class="row justify-center items-center min-h-screen">
    <q-card class="col-12 col-sm-6 col-md-4 q-pa-lg">
      <q-card-section>
        <div class="text-h4 text-center q-mb-md">GrocyScan</div>
        <div class="text-caption text-center text-grey q-mb-lg">Sign in to continue</div>
      </q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="username"
            label="Username"
            outlined
            dense
            :rules="[v => !!v || 'Required']"
          />
          <q-input
            v-model="password"
            type="password"
            label="Password"
            outlined
            dense
            :rules="[v => !!v || 'Required']"
          />
          <q-banner v-if="error" class="bg-negative text-white rounded-borders">
            {{ error }}
          </q-banner>
          <q-btn type="submit" label="Sign In" color="primary" class="full-width" unelevated />
        </q-form>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login } from '../services/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')

onMounted(() => {
  if (!authStore.authEnabled) {
    router.replace('/scan')
  }
})

async function onSubmit() {
  error.value = ''
  try {
    await login(username.value, password.value)
    authStore.setUser(username.value)
    const redirect = route.query.redirect || '/scan'
    router.replace(redirect)
  } catch (e) {
    error.value = e.message || 'Login failed'
  }
}
</script>
