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

      <!-- Admin actions -->
      <div v-if="auth.isAdmin" class="actions">
        <button
          v-if="canGenerateBracket"
          class="btn btn-primary"
          :disabled="actionLoading"
          @click="generateBracket"
        >
          <span v-if="actionLoading" class="spinner"></span>
          {{ actionLoading ? 'Generiranje...' : '⚡ Generiraj bracket' }}
        </button>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <!-- Bracket section -->
      <div v-if="matches.length" class="card section">
        <h2 class="section-title">Bracket</h2>
        <div class="bracket">
          <div v-for="round in rounds" :key="round" class="bracket-round">
            <div class="round-label">{{ roundLabel(round) }}</div>
            <div
              v-for="match in matchesByRound(round)"
              :key="match.match_id"
              class="bracket-match"
              :class="{ completed: match.status === 'completed', clickable: true }"
              @click="openMatchModal(match)"
            >
              <div
                class="bracket-player"
                :class="{ winner: match.winner_id === match.player1_id, bye: !match.player1_id }"
              >
                {{ match.player1_name || 'TBD' }}
                <span v-if="match.player1_stats" class="player-score">{{ match.player1_stats.score }}</span>
              </div>
              <div class="bracket-vs">vs</div>
              <div
                class="bracket-player"
                :class="{ winner: match.winner_id === match.player2_id, bye: !match.player2_id }"
              >
                {{ match.player2_name || 'TBD' }}
                <span v-if="match.player2_stats" class="player-score">{{ match.player2_stats.score }}</span>
              </div>
              <div v-if="match.status === 'pending' && auth.isAdmin" class="match-status-indicator">
                ⏳ Čeka rezultat
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!canGenerateBracket" class="card section">
        <p class="empty-inline">Bracket još nije generiran.</p>
      </div>

    </template>

    <!-- Match Detail Modal -->
    <div v-if="selectedMatch" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>Detalji meča</h3>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <div class="match-info">
            <span class="badge" :class="`badge-${selectedMatch.status}`">{{ matchStatusLabel(selectedMatch.status) }}</span>
            <span v-if="selectedMatch.duration_seconds" class="match-duration">
              ⏱ {{ formatDuration(selectedMatch.duration_seconds) }}
            </span>
          </div>

          <div class="match-players">
            <div class="match-player" :class="{ winner: selectedMatch.winner_id === selectedMatch.player1_id }">
              <div class="player-name">{{ selectedMatch.player1_name || 'TBD' }}</div>
              <div v-if="selectedMatch.player1_stats" class="player-stats">
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player1_stats.kills }}</span>
                  <span class="stat-label">Kills</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player1_stats.deaths }}</span>
                  <span class="stat-label">Deaths</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player1_stats.assists }}</span>
                  <span class="stat-label">Assists</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player1_stats.score }}</span>
                  <span class="stat-label">Score</span>
                </div>
              </div>
            </div>

            <div class="vs-divider">VS</div>

            <div class="match-player" :class="{ winner: selectedMatch.winner_id === selectedMatch.player2_id }">
              <div class="player-name">{{ selectedMatch.player2_name || 'TBD' }}</div>
              <div v-if="selectedMatch.player2_stats" class="player-stats">
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player2_stats.kills }}</span>
                  <span class="stat-label">Kills</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player2_stats.deaths }}</span>
                  <span class="stat-label">Deaths</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player2_stats.assists }}</span>
                  <span class="stat-label">Assists</span>
                </div>
                <div class="stat">
                  <span class="stat-value">{{ selectedMatch.player2_stats.score }}</span>
                  <span class="stat-label">Score</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Admin: Submit Result -->
          <div v-if="auth.isAdmin && selectedMatch.status === 'pending' && selectedMatch.player1_id && selectedMatch.player2_id" class="submit-result">
            <h4>Unesi rezultat</h4>
            
            <div class="result-form">
              <div class="form-group">
                <label>Pobjednik</label>
                <select v-model="resultForm.winner_id">
                  <option value="">-- Odaberi --</option>
                  <option :value="selectedMatch.player1_id">{{ selectedMatch.player1_name }}</option>
                  <option :value="selectedMatch.player2_id">{{ selectedMatch.player2_name }}</option>
                </select>
              </div>

              <div class="form-group">
                <label>Trajanje (sekunde)</label>
                <input v-model.number="resultForm.duration_seconds" type="number" min="0" placeholder="1800" />
              </div>

              <div class="stats-inputs">
                <div class="stats-column">
                  <h5>{{ selectedMatch.player1_name }}</h5>
                  <div class="form-row">
                    <input v-model.number="resultForm.player1_stats.kills" type="number" min="0" placeholder="K" />
                    <input v-model.number="resultForm.player1_stats.deaths" type="number" min="0" placeholder="D" />
                    <input v-model.number="resultForm.player1_stats.assists" type="number" min="0" placeholder="A" />
                    <input v-model.number="resultForm.player1_stats.score" type="number" min="0" placeholder="Score" />
                  </div>
                </div>
                <div class="stats-column">
                  <h5>{{ selectedMatch.player2_name }}</h5>
                  <div class="form-row">
                    <input v-model.number="resultForm.player2_stats.kills" type="number" min="0" placeholder="K" />
                    <input v-model.number="resultForm.player2_stats.deaths" type="number" min="0" placeholder="D" />
                    <input v-model.number="resultForm.player2_stats.assists" type="number" min="0" placeholder="A" />
                    <input v-model.number="resultForm.player2_stats.score" type="number" min="0" placeholder="Score" />
                  </div>
                </div>
              </div>

              <div v-if="submitError" class="alert alert-error">{{ submitError }}</div>

              <button class="btn btn-primary" :disabled="submitLoading || !resultForm.winner_id" @click="submitResult">
                <span v-if="submitLoading" class="spinner"></span>
                {{ submitLoading ? 'Spremanje...' : 'Spremi rezultat' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { tournamentApi, matchApi } from '../api/index.js'
import { authStore as auth } from '../stores/auth.js'

const route = useRoute()
const id = route.params.id

const tournament = ref(null)
const matches = ref([])
const loading = ref(false)
const actionLoading = ref(false)
const error = ref('')
const success = ref('')

// Modal state
const selectedMatch = ref(null)
const submitLoading = ref(false)
const submitError = ref('')
const resultForm = ref({
  winner_id: '',
  duration_seconds: null,
  player1_stats: { kills: 0, deaths: 0, assists: 0, score: 0 },
  player2_stats: { kills: 0, deaths: 0, assists: 0, score: 0 },
})

const canGenerateBracket = computed(() => {
  return tournament.value && 
    ['registration', 'draft'].includes(tournament.value.status) &&
    tournament.value.current_participants >= 2
})

const rounds = computed(() => {
  if (!matches.value.length) return []
  const max = Math.max(...matches.value.map(m => m.round))
  return Array.from({ length: max }, (_, i) => i + 1)
})

function matchesByRound(round) {
  return matches.value.filter(m => m.round === round).sort((a, b) => a.position - b.position)
}

function roundLabel(round) {
  const total = rounds.value.length
  if (round === total) return 'Finale'
  if (round === total - 1) return 'Polufinale'
  if (round === total - 2) return 'Četvrtfinale'
  return `Runda ${round}`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    tournament.value = await tournamentApi.get(id)
    
    // Load matches from match-service
    if (!['registration', 'draft'].includes(tournament.value.status)) {
      try {
        matches.value = await matchApi.byTournament(id)
      } catch (e) {
        // Fallback to bracket from tournament-service
        try {
          const bracket = await tournamentApi.getBracket(id)
          matches.value = bracket.matches || []
        } catch {}
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function generateBracket() {
  error.value = ''
  success.value = ''
  actionLoading.value = true
  try {
    const bracket = await tournamentApi.generateBracket(id)
    matches.value = bracket.matches || []
    tournament.value.status = 'in_progress'
    success.value = 'Bracket uspješno generiran!'
  } catch (e) {
    error.value = e.message
  } finally {
    actionLoading.value = false
  }
}

function openMatchModal(match) {
  selectedMatch.value = match
  submitError.value = ''
  resultForm.value = {
    winner_id: '',
    duration_seconds: null,
    player1_stats: { kills: 0, deaths: 0, assists: 0, score: 0 },
    player2_stats: { kills: 0, deaths: 0, assists: 0, score: 0 },
  }
}

function closeModal() {
  selectedMatch.value = null
}

async function submitResult() {
  submitError.value = ''
  submitLoading.value = true
  try {
    const data = {
      winner_id: resultForm.value.winner_id,
      duration_seconds: resultForm.value.duration_seconds || null,
      player1_stats: resultForm.value.player1_stats,
      player2_stats: resultForm.value.player2_stats,
    }
    await matchApi.submitResult(selectedMatch.value.match_id, data)
    
    // Reload matches
    matches.value = await matchApi.byTournament(id)
    closeModal()
    success.value = 'Rezultat uspješno spremljen!'
  } catch (e) {
    submitError.value = e.message
  } finally {
    submitLoading.value = false
  }
}

function statusLabel(s) {
  const m = { registration: 'Prijave otvorene', in_progress: 'U tijeku', completed: 'Završen', draft: 'Nacrt', cancelled: 'Otkazan' }
  return m[s] || s
}

function matchStatusLabel(s) {
  const m = { pending: 'Čeka', in_progress: 'U tijeku', completed: 'Završen', cancelled: 'Otkazan' }
  return m[s] || s
}

function formatLabel(f) {
  const m = { single_elimination: 'Single Elimination', double_elimination: 'Double Elimination', round_robin: 'Round Robin' }
  return m[f] || f
}

function formatDate(d) {
  return new Date(d).toLocaleString('hr-HR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
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

.bracket {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.bracket-round {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 200px;
}

.round-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 4px;
}

.bracket-match {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: all 0.2s;
}

.bracket-match.clickable {
  cursor: pointer;
}

.bracket-match.clickable:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.bracket-match.completed { border-color: var(--accent); }

.bracket-player {
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.player-score {
  font-size: 12px;
  opacity: 0.8;
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

.match-status-indicator {
  text-align: center;
  font-size: 11px;
  padding: 6px;
  background: var(--surface);
  color: var(--text-muted);
  border-top: 1px solid var(--border);
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 700;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px 8px;
}

.modal-close:hover { color: var(--text); }

.modal-body {
  padding: 20px;
}

.match-info {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

.match-duration {
  font-size: 13px;
  color: var(--text-muted);
}

.match-players {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.match-player {
  flex: 1;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  text-align: center;
}

.match-player.winner {
  border-color: var(--accent);
  background: var(--accent-dim);
}

.player-name {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
}

.match-player.winner .player-name {
  color: var(--accent);
}

.player-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.vs-divider {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-muted);
}

/* Submit result form */
.submit-result {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.submit-result h4 {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 16px;
}

.result-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stats-column h5 {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-muted);
}

.form-row {
  display: flex;
  gap: 8px;
}

.form-row input {
  width: 100%;
  text-align: center;
}

@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr 1fr; }
  .match-players { flex-direction: column; }
  .vs-divider { justify-content: center; padding: 8px 0; }
  .stats-inputs { grid-template-columns: 1fr; }
  .player-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>