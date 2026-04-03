<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="not-found-code">404</div>
      <h1 class="not-found-title">Stranica nije pronadena</h1>
      <p class="not-found-text">Trazena stranica ne postoji ili je uklonjena.</p>
      <router-link to="/tournaments" class="btn btn-primary">Natrag na turnire</router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.not-found-content {
  text-align: center;
}

.not-found-code {
  font-size: 80px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 12px;
}

.not-found-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}

.not-found-text {
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 24px;
}
</style>