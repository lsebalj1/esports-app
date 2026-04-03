<template>
  <div>
    <NavBar v-if="!isGuestPage" />
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'

const route = useRoute()
const isGuestPage = computed(() => route.meta.guest === true)
</script>