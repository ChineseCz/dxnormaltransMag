import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './index.css'

// Global 401 handler for all direct fetch calls across the app.
const _rawFetch = window.fetch.bind(window)
let _redirectingToLogin = false
window.fetch = async (...args) => {
  const res = await _rawFetch(...args)
  if (res.status === 401 && !_redirectingToLogin) {
    _redirectingToLogin = true
    ;['auth_token', 'user_info', 'auth_expires'].forEach((k) => localStorage.removeItem(k))
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    } else {
      _redirectingToLogin = false
    }
  }
  return res
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')

