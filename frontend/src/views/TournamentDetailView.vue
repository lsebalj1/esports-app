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
          <div class="t-meta">
            <span class="t-game">{{ tournament.game }}</span>
            <span class="t-format">{{ tournament.match_format.toUpperCase() }}</span>
            <span class="t-teamsize">{{ tournament.team_size }}v{{ tournament.team_size }}</span>
          </div>
        </div>
        <span class="badge" :class="`badge-${tournament.status}`">{{ statusLabel(tournament.status) }}</span>
      </div>

      <div class="info-grid">
        <div class="info-item card">
          <div class="info-label">Timovi</div>
          <div class="info-value">{{ tournament.current_teams }} / {{ tournament.max_teams }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Format</div>
          <div class="info-value">{{ formatLabel(tournament.format) }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Nagradni fond</div>
          <div class="info-value">{{ tournament.prize_pool ? '$' + Number(tournament.prize_pool).toLocaleString() : '—' }}</div>
        </div>
        <div class="info-item card">
          <div class="info-label">Početak</div>
          <div class="info-value">{{ formatDate(tournament.start_date) }}</div>
        </div>
      </div>

      <!-- Admin -->
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
                class="bracket-team"
                :class="{ winner: match.winner_id === match.team1_id, bye: !match.team1_id }"
              >
                <span class="team-name">{{ match.team1_name || 'TBD' }}</span>
                <span class="team-score">{{ match.team1_maps_won }}</span>
              </div>
              <div class="bracket-vs">
                <span class="match-format-badge">{{ match.match_format }}</span>
              </div>
              <div
                class="bracket-team"
                :class="{ winner: match.winner_id === match.team2_id, bye: !match.team2_id }"
              >
                <span class="team-name">{{ match.team2_name || 'TBD' }}</span>
                <span class="team-score">{{ match.team2_maps_won }}</span>
              </div>
              <div v-if="match.status === 'pending' && auth.isAdmin" class="match-status-indicator">
                 Čeka rezultat
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
            <span class="match-format-label">{{ selectedMatch.match_format?.toUpperCase() }}</span>
            <span v-if="selectedMatch.duration_seconds" class="match-duration">
              ⏱ {{ formatDuration(selectedMatch.duration_seconds) }}
            </span>
          </div>

          <div class="match-score">
            <div class="score-team" :class="{ winner: selectedMatch.winner_id === selectedMatch.team1_id }">
              <div class="score-team-name">{{ selectedMatch.team1_name || 'TBD' }}</div>
              <div class="score-value">{{ selectedMatch.team1_maps_won }}</div>
            </div>
            <div class="score-separator">:</div>
            <div class="score-team" :class="{ winner: selectedMatch.winner_id === selectedMatch.team2_id }">
              <div class="score-value">{{ selectedMatch.team2_maps_won }}</div>
              <div class="score-team-name">{{ selectedMatch.team2_name || 'TBD' }}</div>
            </div>
          </div>

          <div v-if="selectedMatch.map_results?.length" class="map-results">
            <h4>Rezultati po mapama</h4>
            <div class="map-list">
              <div v-for="map in selectedMatch.map_results" :key="map.map_number" class="map-item">
                <span class="map-number">Map {{ map.map_number }}</span>
                <span class="map-name">{{ map.map_name }}</span>
                <span class="map-score">
                  <span :class="{ 'map-winner': map.winner_team_id === selectedMatch.team1_id }">{{ map.team1_score }}</span>
                  :
                  <span :class="{ 'map-winner': map.winner_team_id === selectedMatch.team2_id }">{{ map.team2_score }}</span>
                </span>
              </div>
            </div>
          </div>

          <div v-if="selectedMatch.team1_stats || selectedMatch.team2_stats" class="team-stats-section">
            <h4>Statistike igrača</h4>
            <div class="teams-stats">
              <div class="team-stats-block" v-if="selectedMatch.team1_stats">
                <h5 :class="{ winner: selectedMatch.winner_id === selectedMatch.team1_id }">{{ selectedMatch.team1_name }}</h5>
                <table class="stats-table">
                  <thead>
                    <tr><th>Igrač</th><th>K</th><th>D</th><th>A</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in selectedMatch.team1_stats.players" :key="p.player_id">
                      <td>{{ p.player_name }}</td>
                      <td>{{ p.kills }}</td>
                      <td>{{ p.deaths }}</td>
                      <td>{{ p.assists }}</td>
                      <td>{{ p.score }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="team-stats-block" v-if="selectedMatch.team2_stats">
                <h5 :class="{ winner: selectedMatch.winner_id === selectedMatch.team2_id }">{{ selectedMatch.team2_name }}</h5>
                <table class="stats-table">
                  <thead>
                    <tr><th>Igrač</th><th>K</th><th>D</th><th>A</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in selectedMatch.team2_stats.players" :key="p.player_id">
                      <td>{{ p.player_name }}</td>
                      <td>{{ p.kills }}</td>
                      <td>{{ p.deaths }}</td>
                      <td>{{ p.assists }}</td>
                      <td>{{ p.score }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div v-if="auth.isAdmin && selectedMatch.status === 'pending' && selectedMatch.team1_id && selectedMatch.team2_id" class="submit-result">
            <h4>Unesi rezultat</h4>
            
            <div class="result-form">
              <div class="form-group">
                <label>Pobjednik</label>
                <select v-model="resultForm.winner_id">
                  <option value="">-- Odaberi --</option>
                  <option :value="selectedMatch.team1_id">{{ selectedMatch.team1_name }}</option>
                  <option :value="selectedMatch.team2_id">{{ selectedMatch.team2_name }}</option>
                </select>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>{{ selectedMatch.team1_name }} mape</label>
                  <input v-model.number="resultForm.team1_maps_won" type="number" min="0" :max="getMaxMaps()" />
                </div>
                <div class="form-group">
                  <label>{{ selectedMatch.team2_name }} mape</label>
                  <input v-model.number="resultForm.team2_maps_won" type="number" min="0" :max="getMaxMaps()" />
                </div>
              </div>

              <div class="form-group">
                <label>Trajanje (sekunde)</label>
                <input v-model.number="resultForm.duration_seconds" type="number" min="0" placeholder="3600" />
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

const selectedMatch = ref(null)
const submitLoading = ref(false)
const submitError = ref('')
const resultForm = ref({
  winner_id: '',
  team1_maps_won: 0,
  team2_maps_won: 0,
  duration_seconds: null,
})

const canGenerateBracket = computed(() => {
  return tournament.value && 
    ['registration', 'draft'].includes(tournament.value.status) &&
    tournament.value.current_teams >= 2
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

function getMaxMaps() {
  const format = selectedMatch.value?.match_format || 'bo3'
  if (format === 'bo1') return 1
  if (format === 'bo3') return 2
  return 3
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    tournament.value = await tournamentApi.get(id)
    
    if (!['registration', 'draft'].includes(tournament.value.status)) {
      try {
        matches.value = await matchApi.byTournament(id)
      } catch (e) {
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
    team1_maps_won: 0,
    team2_maps_won: 0,
    duration_seconds: null,
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
      team1_maps_won: resultForm.value.team1_maps_won,
      team2_maps_won: resultForm.value.team2_maps_won,
      duration_seconds: resultForm.value.duration_seconds || null,
    }
    await matchApi.submitResult(selectedMatch.value.match_id, data)
    
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
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

onMounted(load)
</script>

<style scoped>
.back-btn { margin-bottom: 8px; }

.t-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 4px;
}

.t-game { color: var(--accent); font-size: 14px; font-weight: 600; }
.t-format { 
  font-size: 11px; 
  font-weight: 700; 
  padding: 2px 8px; 
  background: var(--accent-dim); 
  color: var(--accent); 
  border-radius: 4px; 
}
.t-teamsize { font-size: 13px; color: var(--text-muted); }

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
  min-width: 220px;
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
  cursor: pointer;
}

.bracket-match:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.bracket-match.completed { border-color: var(--accent); }

.bracket-team {
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bracket-team.winner {
  background: var(--accent-dim);
}

.bracket-team.winner .team-name {
  color: var(--accent);
  font-weight: 700;
}

.bracket-team.bye {
  color: var(--text-muted);
  font-style: italic;
}

.team-score {
  font-size: 16px;
  font-weight: 700;
  min-width: 24px;
  text-align: center;
}

.bracket-team.winner .team-score {
  color: var(--accent);
}

.bracket-vs {
  text-align: center;
  padding: 4px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.match-format-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
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
  max-width: 700px;
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

.modal-header h3 { font-size: 16px; font-weight: 700; }

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px 8px;
}

.modal-close:hover { color: var(--text); }

.modal-body { padding: 20px; }

.match-info {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

.match-format-label {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  background: var(--surface2);
  border-radius: 4px;
}

.match-duration { font-size: 13px; color: var(--text-muted); }

/* Score display */
.match-score {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--surface2);
  border-radius: var(--radius);
}

.score-team {
  display: flex;
  align-items: center;
  gap: 16px;
}

.score-team:first-child { flex-direction: row; }
.score-team:last-child { flex-direction: row-reverse; }

.score-team-name { font-size: 16px; font-weight: 600; }
.score-value { font-size: 32px; font-weight: 700; }
.score-team.winner .score-team-name { color: var(--accent); }
.score-team.winner .score-value { color: var(--accent); }
.score-separator { font-size: 24px; color: var(--text-muted); }

/* Map results */
.map-results { margin-bottom: 24px; }
.map-results h4 { font-size: 14px; font-weight: 700; margin-bottom: 12px; }

.map-list { display: flex; flex-direction: column; gap: 8px; }

.map-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--surface2);
  border-radius: var(--radius-sm);
}

.map-number { font-size: 11px; color: var(--text-muted); font-weight: 700; }
.map-name { flex: 1; font-size: 13px; }
.map-score { font-weight: 700; }
.map-winner { color: var(--accent); }

/* Team stats */
.team-stats-section h4 { font-size: 14px; font-weight: 700; margin-bottom: 12px; }
.teams-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.team-stats-block h5 { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.team-stats-block h5.winner { color: var(--accent); }

.stats-table {
  width: 100%;
  font-size: 12px;
  border-collapse: collapse;
}

.stats-table th, .stats-table td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.stats-table th {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 11px;
  text-transform: uppercase;
}

.stats-table td:first-child { font-weight: 500; }
.stats-table td:not(:first-child) { text-align: center; }
.stats-table th:not(:first-child) { text-align: center; }

/* Submit result form */
.submit-result {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.submit-result h4 { font-size: 14px; font-weight: 700; margin-bottom: 16px; }

.result-form { display: flex; flex-direction: column; gap: 16px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr 1fr; }
  .teams-stats { grid-template-columns: 1fr; }
  .match-score { flex-direction: column; gap: 12px; }
  .score-team { flex-direction: column !important; gap: 4px; }
}
</style>