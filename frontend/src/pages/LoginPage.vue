<template>
  <div class="row justify-center items-center min-h-screen">
    <q-card class="col-12 col-sm-6 col-md-4 q-pa-lg" data-testid="login-card">
      <q-card-section>
        <div class="text-h4 text-center q-mb-md" data-testid="login-title">{{ configStore.appTitle }}</div>
        <div class="text-caption text-center text-grey q-mb-lg">Sign in to continue</div>
      </q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md" data-testid="login-form">
          <q-input
            v-model="username"
            label="Username"
            outlined
            dense
            data-testid="login-username"
            :rules="[v => !!v || 'Required']"
          />
          <q-input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            label="Password"
            outlined
            dense
            data-testid="login-password"
            :rules="[v => !!v || 'Required']"
          >
            <template v-slot:append>
              <q-icon
                :name="showPassword ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                data-testid="login-password-toggle"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>
          <q-banner v-if="error" class="bg-negative text-white rounded-borders" data-testid="login-error">
            {{ error }}
          </q-banner>
          <q-btn type="submit" label="Sign In" color="primary" class="full-width" unelevated data-testid="login-submit" />
        </q-form>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useConfigStore } from '../stores/config'
import { login } from '../services/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const configStore = useConfigStore()

const username = ref('')
const password = ref('')
const error = ref('')
const showPassword = ref(false)

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
