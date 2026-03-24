<template>
  <div class="page">
    <div v-if="loading" class="loading">
      <div class="spinner"></div> Učitavanje...
    </div>

    <template v-else-if="tournament">
      <div class="page-header">
        <div>
          <button class="btn btn-secondary btn-sm back-btn" @click="$router.push('/tournaments')">← Natrag</button>
          <h1 class="page-title">{{ tournament.name }}</h1>
          <div class="t-game">{{ tournament.game }}</div>
        </div>
        <span class="badge" :class="`badge-${tournament.status}`">{{ statusLabel(tournament.status) }}</span>
      </div>
      <div class="info-grid">
        <div class="info-item card">
          <div class="info-label">Igrači</div>
          <div class="info-value">{{ tournament.current_participants }} / {{ tournament.max_participants }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Format</div>
          <div class="info-value">{{ formatLabel(tournament.format) }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Nagradni fond</div>
          <div class="info-value">{{ tournament.prize_pool ? '$' + tournament.prize_pool : '—' }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Početak</div>
          <div class="info-value">{{ formatDate(tournament.start_date) }}</div>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="actions">
        <template v-if="auth.isLoggedIn && tournament.status === 'registration' && !auth.isOrganizer">
          <button v-if="!isRegistered" class="btn btn-primary" :disabled="actionLoading" @click="register">
            <span v-if="actionLoading" class="spinner"></span>
            Prijavi se na turnir
          </button>
          <button v-else class="btn btn-danger" :disabled="actionLoading" @click="unregister">
            <span v-if="actionLoading" class="spinner"></span>
            Odjavi se
          </button>
        </template>
      </div>

      <div v-if="bracket" class="card section">
        <h2 class="section-title">Bracket</h2>
        <div class="bracket">
          <div v-for="round in rounds" :key="round" class="bracket-round">
            <div class="round-label">Runda {{ round }}</div>
            <div
              v-for="match in matchesByRound(round)"
              :key="match.match_id"
              class="bracket-match"
              :class="{ completed: match.status === 'completed' }"
            >
              <div
                class="bracket-player"
                :class="{ winner: match.winner_id === match.player1_id, bye: !match.player1_id }"
              >
                {{match.player1_name || 'TBD'}}
              </div>
              <div class="bracket-vs">vs</div>
              <div
                class="bracket-player"
                :class="{ winner: match.winner_id === match.player2_id, bye: !match.player2_id }"
              >
                {{match.player2_name || 'TBD'}}
              </div>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { tournamentApi } from '../api/index.js'
import { authStore as auth } from '../stores/auth.js'

const route = useRoute()
const id = route.params.id

const tournament = ref(null)
const bracket = ref(null)
const loading = ref(false)
const actionLoading = ref(false)
const error = ref('')
const success = ref('')

const participants = computed(() => tournament.value?.participants || [])

const isRegistered = computed(() =>
  auth.isLoggedIn && participants.value.some(p => p.user_id === auth.user?.user_id)
)

const rounds = computed(() => {
  if (!bracket.value) return []
  const max = Math.max(...bracket.value.matches.map(m => m.round))
  return Array.from({ length: max }, (_, i) => i + 1)
})

function matchesByRound(round) {
  return bracket.value?.matches.filter(m => m.round === round) || []
}

async function load() {
  loading.value = true
  try {
    tournament.value = await tournamentApi.get(id)
    if (tournament.value.status !== 'registration' && tournament.value.status !== 'draft') {
      try { bracket.value = await tournamentApi.getBracket(id) } catch {}
    }
  } finally {
    loading.value = false
  }
}

async function register() {
  error.value = ''; success.value = ''
  actionLoading.value = true
  try {
    await tournamentApi.register(id)
    success.value = 'Uspješno si se prijavio!'
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    actionLoading.value = false
  }
}

async function unregister() {
  error.value = ''; success.value = ''
  actionLoading.value = true
  try {
    await tournamentApi.unregister(id)
    success.value = 'Odjavljen si s turnira.'
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    actionLoading.value = false
  }
}

async function generateBracket() {
  error.value = ''; success.value = ''
  actionLoading.value = true
  try {
    bracket.value = await tournamentApi.generateBracket(id)
    tournament.value.status = 'in_progress'
    success.value = 'Bracket uspješno generiran!'
  } catch (e) {
    error.value = e.message
  } finally {
    actionLoading.value = false
  }
}

function statusLabel(s) {
  const m = { registration: 'Registracija', in_progress: 'U tijeku', completed: 'Završen', draft: 'Nacrt', cancelled: 'Otkazan' }
  return m[s] || s
}

function formatLabel(f) {
  const m = { single_elimination: 'Single Elimination', double_elimination: 'Double Elimination', round_robin: 'Round Robin' }
  return m[f] || f
}

function formatDate(d) {
  return new Date(d).toLocaleString('hr-HR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.back-btn { margin-bottom: 8px; }
.t-game { color: var(--accent); font-size: 14px; margin-top: 2px; }

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.info-item { text-align: center; }
.info-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 4px; }
.info-value { font-size: 18px; font-weight: 700; }

.actions { display: flex; gap: 10px; margin-bottom: 20px; }

.section { margin-top: 20px; }
.section-title { font-size: 16px; font-weight: 700; margin-bottom: 16px; }

.empty-inline { color: var(--text-muted); font-size: 14px; }

.participants-list { display: flex; flex-wrap: wrap; gap: 8px; }
.participant-item {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 14px;
  font-size: 13px;
}

/* ── Bracket ──────────────────────────────────────────────── */
.bracket {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.bracket-round {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 180px;
}

.round-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  font-weight: 700;
  margin-bottom: 4px;
}

.bracket-match {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: border-color 0.2s;
}

.bracket-match.completed { border-color: var(--accent); }

.bracket-player {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
}

.bracket-player.winner {
  background: var(--accent-dim);
  color: var(--accent);
  font-weight: 700;
}

.bracket-player.bye {
  color: var(--text-muted);
  font-style: italic;
}

.bracket-vs {
  text-align: center;
  font-size: 10px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 2px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr 1fr; }
}
</style>
