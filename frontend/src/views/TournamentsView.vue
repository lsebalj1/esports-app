<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Turniri</h1>
      <button v-if="auth.isAdmin" class="btn btn-primary" @click="showForm = !showForm">
        {{ showForm ? 'X' : '+ Novi turnir' }}
      </button>
    </div>

    <div v-if="showForm" class="card create-form">
      <h2 class="form-title">Novi turnir</h2>
      <div v-if="createError" class="alert alert-error">{{ createError }}</div>

      <div class="form-row">
        <div class="form-group">
          <label>Naziv</label>
          <input v-model="form.name" type="text" placeholder="Ignite 2026" />
        </div>
        <div class="form-group">
          <label>Igra</label>
          <select v-model="form.game">
            <option value="">-- Odaberi igru --</option>
            <option value="CS2">CS2</option>
            <option value="Valorant">Valorant</option>
            <option value="League of Legends">League of Legends</option>
            <option value="Dota 2">Dota 2</option>
            <option value="Fortnite">Fortnite</option>
            <option value="Rocket League">Rocket League</option>
            <option value="Overwatch 2">Overwatch 2</option>
            <option value="Apex Legends">Apex Legends</option>
            <option value="Rainbow Six Siege">Rainbow Six Siege</option>
            <option value="Marvel Rivals">Marvel Rivals</option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Format</label>
          <select v-model="form.format">
            <option value="single_elimination">Single Elimination</option>
            <option value="double_elimination">Double Elimination</option>
            <option value="round_robin">Round Robin</option>
          </select>
        </div>
        <div class="form-group">
          <label>Max igrača</label>
          <input v-model.number="form.max_participants" type="number" min="2" max="256" />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Nagradni fond ($)</label>
          <input v-model.number="form.prize_pool" type="number" min="0" placeholder="0" />
        </div>
        <div class="form-group">
          <label>Datum početka</label>
          <input v-model="form.start_date" type="datetime-local" />
        </div>
      </div>

      <button class="btn btn-primary" :disabled="creating" @click="createTournament">
        <span v-if="creating" class="spinner"></span>
        {{ creating ? 'Kreiranje...' : 'Kreiraj turnir' }}
      </button>
    </div>

    <div class="filters">
      <button
        v-for="f in filters"
        :key="f.value"
        class="filter-btn"
        :class="{ active: activeFilter === f.value }"
        @click="setFilter(f.value)"
      >
        {{ f.label }}
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div> Učitavanje...
    </div>

    <div v-else-if="!tournaments.length" class="empty">
      <div class="empty-text">Nema turnira.</div>
    </div>

    <div v-else class="tournament-list">
      <div
        v-for="t in tournaments"
        :key="t.tournament_id"
        class="tournament-card card"
        @click="$router.push(`/tournaments/${t.tournament_id}`)"
      >
        <div class="tc-header">
          <div>
            <div class="tc-name">{{ t.name }}</div>
            <div class="tc-game">{{ t.game }}</div>
          </div>
          <span class="badge" :class="`badge-${t.status}`">{{ statusLabel(t.status) }}</span>
        </div>

        <div class="tc-meta">
          <span>{{ t.current_participants }} / {{ t.max_participants }}</span>
          <span>{{ formatLabel(t.format) }}</span>
          <span v-if="t.prize_pool">${{ t.prize_pool }}</span>
          <span>{{ formatDate(t.start_date) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tournamentApi } from '../api/index.js'
import { authStore as auth } from '../stores/auth.js'

const tournaments = ref([])
const loading = ref(false)
const showForm = ref(false)
const creating = ref(false)
const createError = ref('')
const activeFilter = ref('')

const filters = [
  {label: 'Svi', value: ''},
  {label: 'U tijeku', value: 'in_progress'},
  {label: 'Završeni', value: 'completed'},
]

const form = ref({
  name: '',
  game: '',
  format: 'single_elimination',
  max_participants: 8,
  prize_pool: null,
  start_date: '',
})

async function load() {
  loading.value = true
  try {
    const params = activeFilter.value ? { status: activeFilter.value } : {}
    tournaments.value = await tournamentApi.list(params)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function setFilter(val) {
  activeFilter.value = val
  await load()
}

async function createTournament() {
  createError.value = ''
  if (!form.value.name || !form.value.game || !form.value.start_date) {
    createError.value = 'Popuni naziv, igru i datum.'
    return
  }
  creating.value = true
  try {
    const payload = {
      ...form.value,
      start_date: new Date(form.value.start_date).toISOString(),
      prize_pool: form.value.prize_pool || null,
    }
    await tournamentApi.create(payload)
    showForm.value = false
    form.value = { name: '', game: '', format: 'single_elimination', max_participants: 8, prize_pool: null, start_date: '' }
    await load()
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

function statusLabel(s) {
  const m = { registration: 'View', in_progress: 'U tijeku', completed: 'Završen', draft: 'Nacrt', cancelled: 'Otkazan' }
  return m[s] || s
}

function formatLabel(f) {
  const m = { single_elimination: 'Single Elim.', double_elimination: 'Double Elim.', round_robin: 'Round Robin' }
  return m[f] || f
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('hr-HR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

onMounted(load)
</script>

<style scoped>
.create-form {
  margin-bottom: 24px;
}

.form-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover,
.filter-btn.active {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: var(--accent);
}

.tournament-list { display: flex; flex-direction: column; gap: 12px; }

.tournament-card {
  cursor: pointer;
  transition: border-color 0.2s, transform 0.1s;
}

.tournament-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.tc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.tc-name {
  font-size: 16px;
  font-weight: 700;
}

.tc-game {
  font-size: 13px;
  color: var(--accent);
  margin-top: 2px;
}

.tc-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 10px;
}
</style>
