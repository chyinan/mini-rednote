<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const categories = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]

const selectCategory = (cat) => {
  router.push({ path: '/', query: { category: cat } })
}
</script>

<template>
  <div class="min-h-screen bg-white p-4">
    <h1 class="text-xl font-bold mb-6 text-center pt-2">全部分区</h1>
    <div class="grid grid-cols-3 gap-4">
      <button 
        v-for="cat in categories" 
        :key="cat"
        @click="selectCategory(cat)"
        class="aspect-[1.5] flex items-center justify-center bg-gray-50 rounded-xl text-gray-700 font-medium hover:bg-gray-100 transition-colors text-base"
      >
        {{ cat }}
      </button>
    </div>
  </div>
</template>

