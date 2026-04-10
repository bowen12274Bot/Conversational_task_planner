<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getPingMessage } from './services/api'

const status = ref('Checking backend connection...')

onMounted(async () => {
  try {
    status.value = await getPingMessage()
  } catch (error) {
    status.value =
      error instanceof Error ? `Connection failed: ${error.message}` : 'Connection failed'
  }
})
</script>

<template>
  <main class="app-shell">
    <section class="status-card">
      <p class="eyebrow">Conversational Task Planner</p>
      <h1>Frontend Ready</h1>
      <p class="description">This page calls the backend test API at <code>/api/ping</code>.</p>
      <p class="status">{{ status }}</p>
    </section>
  </main>
</template>
