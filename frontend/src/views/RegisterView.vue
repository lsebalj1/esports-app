<template>
  <div class="auth-page">
    <div class="auth-card card">
      <div class="auth-header">
        <div class="auth-icon">⚔️</div>
        <h1 class="auth-title">Registracija</h1>
        <p class="auth-sub">Pridruži se platformi</p>
      </div>

      <div v-if="error" class="alert alert-error">{{error}}</div>

      <div class="form-group">
        <label>Korisničko ime</label>
        <input v-model="username" type="text" placeholder="ProGamer123" />
      </div>

      <div class="form-group">
        <label>Email</label>
        <input v-model="email" type="email" placeholder="tvoj@email.com" />
      </div>

      <div class="form-group">
        <label>Lozinka</label>
        <input v-model="password" type="password" placeholder="min. 8 znakova" />
      </div>

      <div class="form-group">
        <label>Uloga</label>
        <select v-model="role">
          <option value="player">🎮 Igrač</option>
          <option value="organizer">🏆 Organizator</option>
        </select>
      </div>

      <button class="btn btn-primary btn-full" :disabled="loading" @click="submit">
        <span v-if="loading" class="spinner"></span>
        {{loading ? 'Registracija...' : 'Registriraj se'}}
      </button>

      <p class="auth-footer">
        Već imaš račun? <router-link to="/login">Prijavi se</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../stores/auth.js'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const role = ref('player')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (!username.value || !email.value || !password.value) {
    error.value = 'Popuni sva polja.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Lozinka mora imati najmanje 8 znakova.'
    return
  }
  loading.value = true
  try {
    await authStore.register(username.value, email.value, password.value, role.value)
    router.push('/tournaments')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
}

.auth-header {
  text-align: center;
  margin-bottom: 28px;
}

.auth-icon { font-size: 40px; margin-bottom: 12px; }
.auth-title { font-size: 22px; font-weight: 700; }
.auth-sub { color: var(--text-muted); font-size: 14px; margin-top: 4px; }

.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: var(--text-muted);
}
</style>
