import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../stores/auth.js'

import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import TournamentsView from '../views/TournamentsView.vue'
import TournamentDetailView from '../views/TournamentDetailView.vue'

const routes = [
  {path: '/', redirect: '/tournaments' },
  {path: '/login', component: LoginView, meta: { guest: true } },
  {path: '/register', component: RegisterView, meta: { guest: true } },
  {path: '/tournaments', component: TournamentsView },
  {path: '/tournaments/:id', component: TournamentDetailView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.guest && authStore.isLoggedIn) return '/tournaments'
})

export default router
