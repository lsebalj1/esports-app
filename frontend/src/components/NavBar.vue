<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/tournaments" class="navbar-brand">
         <span>EsportsApp</span>
      </router-link>

      <div class="navbar-links">
        <router-link to="/tournaments">Svi turniri</router-link>
        
        <div class="game-dropdown" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false">
          <button class="dropdown-trigger">
            Igre <span class="arrow">▼</span>
          </button>
          <div v-if="showDropdown" class="dropdown-menu">
            <router-link 
              v-for="game in games" 
              :key="game.value" 
              :to="`/tournaments?game=${encodeURIComponent(game.value)}`"
              class="dropdown-item"
              @click="showDropdown = false"
            >
              {{ game.label }}
            </router-link>
          </div>
        </div>

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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore as auth } from '../stores/auth.js'

const router = useRouter()
const showDropdown = ref(false)

const games = [
  { value: 'CS2', label: 'CS2' },
  { value: 'Valorant', label: 'Valorant' },
  { value: 'League of Legends', label: 'League of Legends' },
  { value: 'Dota 2', label: 'Dota 2' },
  { value: 'Fortnite', label: 'Fortnite' },
  { value: 'Rocket League', label: 'Rocket League' },
  { value: 'Overwatch 2', label: 'Overwatch 2' },
  { value: 'Apex Legends', label: 'Apex Legends' },
  { value: 'Rainbow Six Siege', label: 'Rainbow Six Siege' },
  { value: 'Marvel Rivals', label: 'Marvel Rivals' },
]

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

.navbar-links > a {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
}

.navbar-links > a:hover,
.navbar-links > a.router-link-active { color: var(--text); }

.game-dropdown {
  position: relative;
}

.dropdown-trigger {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 0;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}

.dropdown-trigger:hover {
  color: var(--text);
}

.arrow {
  font-size: 10px;
  transition: transform 0.2s;
}

.game-dropdown:hover .arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 0;
  min-width: 180px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 200;
}

.dropdown-item {
  display: block;
  padding: 10px 16px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
}

.dropdown-item:hover {
  background: var(--accent-dim);
  color: var(--accent);
}

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