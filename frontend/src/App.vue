<script setup>
import { RouterLink, RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
</script>

<template>
  <NavBar />
  <div class="min-h-screen bg-xhs-bg">
    <RouterView />
  </div>
</template>

<style scoped>
</style>



