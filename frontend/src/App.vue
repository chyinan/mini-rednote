<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import MobileTabBar from './components/MobileTabBar.vue'

const route = useRoute()
</script>

<template>
  <NavBar v-if="!route.meta.hideNavBar" />
  <div class="min-h-screen bg-xhs-bg pb-16 md:pb-0">
    <RouterView />
  </div>
  <MobileTabBar v-if="!route.meta.hideTabBar" />
</template>

<style scoped>
</style>



