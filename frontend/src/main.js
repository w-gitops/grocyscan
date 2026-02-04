import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar } from 'quasar'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'

import App from './App.vue'
import router from './router'
import { getMe } from './services/api'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(Quasar, { plugins: {} })

router.isReady().then(async () => {
  try {
    const me = await getMe()
    if (me) useAuthStore().setUser(me.username || 'user')
  } catch {
    // no session
  }
  app.mount('#app')
})
