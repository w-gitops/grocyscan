import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar, Notify, Dialog } from 'quasar'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'

import App from './App.vue'
import router from './router'
import { getMe } from './services/api'
import { useAuthStore } from './stores/auth'
import { useConfigStore } from './stores/config'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(Quasar, { plugins: { Notify, Dialog } })

  const configStore = useConfigStore(pinia)
  await configStore.load()
  document.title = configStore.version
    ? `${configStore.appTitle} · ${configStore.version}`
    : configStore.appTitle

  const authStore = useAuthStore(pinia)
  try {
    const me = await getMe()
    if (me) authStore.setUser(me.username || 'user')
  } catch {
    // no session
  }

  app.use(router)
  await router.isReady()
  app.mount('#app')
}

bootstrap()
