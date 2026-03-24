const BASE = {
  auth: '/api/auth',
  tournaments: '/api/tournaments',
  matches: '/api/matches',
  stats: '/api/stats',
}

function getToken() {
  return localStorage.getItem('token')
}

async function request(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(url, { ...options, headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  // 204 No Content
  if (res.status === 204) return null
  return res.json()
}

export const authApi = {
  register: (data) => request(`${BASE.auth}/auth/register`, { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request(`${BASE.auth}/auth/login`, { method: 'POST', body: JSON.stringify(data) }),
  me: () => request(`${BASE.auth}/auth/me`),
}

export const tournamentApi = {
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString()
    return request(`${BASE.tournaments}${q ? '?' + q : ''}`)
  },
  get: (id) => request(`${BASE.tournaments}/${id}`),
  create: (data) => request(`${BASE.tournaments}`, { method: 'POST', body: JSON.stringify(data) }),
  register: (id) => request(`${BASE.tournaments}/${id}/register`, { method: 'POST' }),
  unregister: (id) => request(`${BASE.tournaments}/${id}/register`, { method: 'DELETE' }),
  getBracket: (id) => request(`${BASE.tournaments}/${id}/bracket`),
  generateBracket: (id) => request(`${BASE.tournaments}/${id}/bracket/generate`, { method: 'POST' }),
}

export const matchApi = {
  byTournament: (tournamentId) => request(`${BASE.matches}/tournament/${tournamentId}`),
  get: (id) => request(`${BASE.matches}/${id}`),
  submitResult: (id, data) => request(`${BASE.matches}/${id}/result`, { method: 'POST', body: JSON.stringify(data) }),
}

export const statsApi = {
  leaderboard: () => request(`${BASE.stats}/leaderboard`),
  player: (id) => request(`${BASE.stats}/player/${id}`),
}
