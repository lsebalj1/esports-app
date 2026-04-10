<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <template v-if="gameFilter">{{ gameFilter }}</template>
          <template v-else>Turniri</template>
        </h1>
        <button v-if="gameFilter" class="clear-filter" @click="clearGameFilter">
          Prikazi sve igre
        </button>
      </div>
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
          <label>Match format</label>
          <select v-model="form.match_format">
            <option value="bo1">BO1</option>
            <option value="bo3">BO3</option>
            <option value="bo5">BO5</option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Max timova</label>
          <input v-model.number="form.max_teams" type="number" min="2" max="256" />
        </div>
        <div class="form-group">
          <label>Nagradni fond ($)</label>
          <input v-model.number="form.prize_pool" type="number" min="0" placeholder="0" />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Datum pocetka</label>
          <input v-model="form.start_date" type="datetime-local" />
        </div>
        <div class="form-group"></div>
      </div>

      <button class="btn btn-primary" :disabled="creating" @click="createTournament">
        <span v-if="creating" class="spinner"></span>
        {{ creating ? 'Kreiranje...' : 'Kreiraj turnir' }}
      </button>
    </div>

    <div class="search-box">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Pretrazi turnire po imenu ili igri..."
        class="search-input"
      />
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
      <div class="spinner"></div> Ucitavanje...
    </div>

    <div v-else-if="!filteredTournaments.length" class="empty">
      <div class="empty-text">{{ searchQuery ? 'Nema rezultata pretrage.' : 'Nema turnira.' }}</div>
    </div>

    <div v-else class="tournament-grid">
      <div
        v-for="t in filteredTournaments"
        :key="t.tournament_id"
        class="tournament-card"
        :style="cardStyle(t.game)"
        @click="$router.push(`/tournaments/${t.tournament_id}`)"
      >
        <div class="tc-accent-bar" :style="{ background: gameColor(t.game) }"></div>
        <div class="tc-body">
          <div class="tc-header">
            <div>
              <div class="tc-name">{{ t.name }}</div>
              <div class="tc-game" :style="{ color: gameColor(t.game) }">{{ t.game }}</div>
            </div>
            <span class="badge" :class="`badge-${t.status}`">{{ statusLabel(t.status) }}</span>
          </div>

          <div class="tc-meta">
            <span>{{ t.current_teams }} / {{ t.max_teams }} timova</span>
            <span>{{ formatLabel(t.format) }}</span>
            <span v-if="t.prize_pool" class="tc-prize">${{ Number(t.prize_pool).toLocaleString() }}</span>
          </div>

          <div class="tc-footer">
            <span class="tc-date">{{ formatDate(t.start_date) }}</span>
            <span class="tc-format-badge" :style="{ background: gameColor(t.game) + '22', color: gameColor(t.game) }">{{ t.match_format?.toUpperCase() }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { tournamentApi } from '../api/index.js'
import { authStore as auth } from '../stores/auth.js'

const route = useRoute()
const router = useRouter()

const tournaments = ref([])
const loading = ref(false)
const showForm = ref(false)
const creating = ref(false)
const createError = ref('')
const activeFilter = ref('')
const searchQuery = ref('')

const gameFilter = computed(() => route.query.game || '')

const filters = [
  {label: 'Svi', value: ''},
  {label: 'Prijave', value: 'registration'},
  {label: 'U tijeku', value: 'in_progress'},
  {label: 'Zavrseni', value: 'completed'},
]

const GAME_COLORS = {
  'CS2': '#E8A946',
  'Valorant': '#FF4655',
  'League of Legends': '#C89B3C',
  'Dota 2': '#E44D2E',
  'Fortnite': '#9D4DFF',
  'Rocket League': '#0088FF',
  'Overwatch 2': '#FA9C1E',
  'Apex Legends': '#DA292A',
  'Rainbow Six Siege': '#5A88C4',
  'Marvel Rivals': '#7C6AFF',
}

function gameColor(game) {
  return GAME_COLORS[game] || '#7C6AFF'
}

function cardStyle(game) {
  const color = gameColor(game)
  return {
    borderColor: color + '30',
  }
}

const filteredTournaments = computed(() => {
  if (!searchQuery.value.trim()) return tournaments.value
  const q = searchQuery.value.toLowerCase()
  return tournaments.value.filter(t =>
    t.name.toLowerCase().includes(q) || t.game.toLowerCase().includes(q)
  )
})

const form = ref({
  name: '',
  game: '',
  format: 'single_elimination',
  match_format: 'bo3',
  max_teams: 8,
  prize_pool: null,
  start_date: '',
})

async function load() {
  loading.value = true
  try {
    const params = {}
    if (activeFilter.value) params.status = activeFilter.value
    if (gameFilter.value) params.game = gameFilter.value
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

function clearGameFilter() {
  router.push('/tournaments')
}

watch(() => route.query.game, () => {
  load()
})

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
    form.value = { name: '', game: '', format: 'single_elimination', match_format: 'bo3', max_teams: 8, prize_pool: null, start_date: '' }
    await load()
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

function statusLabel(s) {
  const m = { registration: 'Prijave', in_progress: 'U tijeku', completed: 'Zavrsen', draft: 'Nacrt', cancelled: 'Otkazan' }
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

.search-box {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 11px 16px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
}

.search-input::placeholder {
  color: var(--text-muted);
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

.tournament-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.tournament-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.2s, box-shadow 0.2s;
}

.tournament-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.tc-accent-bar {
  height: 3px;
  width: 100%;
}

.tc-body {
  padding: 18px 20px 16px;
}

.tc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.tc-name {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
}

.tc-game {
  font-size: 12px;
  font-weight: 600;
  margin-top: 3px;
  letter-spacing: 0.02em;
}

.tc-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.tc-prize {
  font-weight: 600;
  color: var(--success);
}

.tc-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.tc-date {
  font-size: 12px;
  color: var(--text-muted);
}

.tc-format-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.04em;
}

.clear-filter {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 0;
  margin-top: 4px;
  transition: color 0.2s;
}

.clear-filter:hover {
  color: var(--accent);
}

@media (max-width: 680px) {
  .tournament-grid {
    grid-template-columns: 1fr;
  }
}
</style>