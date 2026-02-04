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

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(Quasar, { plugins: { Notify, Dialog } })

router.isReady().then(async () => {
  const configStore = useConfigStore()
  await configStore.load()
  document.title = configStore.appTitle
  try {
    const me = await getMe()
    if (me) useAuthStore().setUser(me.username || 'user')
  } catch {
    // no session
  }
  app.mount('#app')
})
