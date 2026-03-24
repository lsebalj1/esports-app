<template>
  <div class="auth-page">
    <div class="auth-card card">
      <div class="auth-header">
        <div class="auth-icon">🎮</div>
        <h1 class="auth-title">Prijava</h1>
        <p class="auth-sub">Dobrodošao natrag</p>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="form-group">
        <label>Email</label>
        <input v-model="email" type="email" placeholder="tvoj@email.com" @keyup.enter="submit" />
      </div>

      <div class="form-group">
        <label>Password</label>
        <input v-model="password" type="password" placeholder="••••••••" @keyup.enter="submit" />
      </div>

      <button class="btn btn-primary btn-full" :disabled="loading" @click="submit">
        <span v-if="loading" class="spinner"></span>
        {{ loading ? 'Login' : 'Login' }}
      </button>

      <p class="auth-footer">
        Nemaš račun? <router-link to="/register">Registriraj se</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../stores/auth.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = 'Popuni sva polja.'
    return
  }
  loading.value = true
  try {
    await authStore.login(email.value, password.value)
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
