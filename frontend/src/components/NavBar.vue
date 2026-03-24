<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/tournaments" class="navbar-brand">
         <span>EsportsApp</span>
      </router-link>

      <div class="navbar-links">
        <router-link to="/tournaments">Turniri</router-link>

        <template v-if="auth.isLoggedIn">
          <div class="navbar-user">
            <span class="user-badge">{{ auth.user.role }}</span>
            <span class="user-name">{{ auth.user.username }}</span>
            <button class="btn btn-secondary btn-sm" @click="logout">Odjava</button>
          </div>
        </template>

        <template v-else>
          <router-link to="/login">Prijava</router-link>
          <router-link to="/register" class="btn btn-primary btn-sm">Registracija</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { authStore as auth } from '../stores/auth.js'

const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.navbar-brand span { color: var(--accent); }

.navbar-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.navbar-links a {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
}

.navbar-links a:hover,
.navbar-links a.router-link-active { color: var(--text); }

.navbar-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
}

.user-badge {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 20px;
  background: var(--accent-dim);
  color: var(--accent);
  letter-spacing: 0.05em;
}
</style>
