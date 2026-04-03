import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../stores/auth.js'

import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import TournamentsView from '../views/TournamentsView.vue'
import TournamentDetailView from '../views/TournamentDetailView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  {path: '/', redirect: () => authStore.isLoggedIn ? '/tournaments' : '/login' },
  {path: '/login', component: LoginView, meta: { guest: true } },
  {path: '/register', component: RegisterView, meta: { guest: true } },
  {path: '/tournaments', component: TournamentsView, meta: { auth: true } },
  {path: '/tournaments/:id', component: TournamentDetailView, meta: { auth: true } },
  {path: '/:pathMatch(.*)*', component: NotFoundView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.guest && authStore.isLoggedIn) return '/tournaments'
  if (to.meta.auth && !authStore.isLoggedIn) return '/login'
})

export default router