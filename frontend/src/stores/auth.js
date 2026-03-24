import {reactive} from 'vue'
import {authApi} from '../api/index.js'

export const authStore = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null,

  get isLoggedIn() {
    return !!this.token
  },

  get isAdmin() {
    return this.user?.role === 'admin'
  },

  async login(email, password) {
    const data = await authApi.login({ email, password })
    this.token = data.access_token
    this.user = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
  },

  async register(username, email, password, role) {
    const data = await authApi.register({ username, email, password, role })
    this.token = data.access_token
    this.user = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
  },

  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },
})
