<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getConversations, getImageUrl } from '../api'
import moment from 'moment'
import 'moment/dist/locale/zh-cn'

moment.locale('zh-cn')

const userStore = useUserStore()
const router = useRouter()
const conversations = ref([])
const loading = ref(true)

const fetchConversations = async () => {
  if (!userStore.user) return
  try {
    const res = await getConversations(userStore.user.id)
    conversations.value = res.data.conversations
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatTime = (timestamp) => {
  return moment(timestamp).fromNow()
}

const goToChat = (userId) => {
  router.push(`/messages/${userId}`)
}

onMounted(() => {
  fetchConversations()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-2xl">
    <h1 class="text-xl font-bold mb-6">消息列表</h1>
    
    <div v-if="loading" class="text-center py-10 text-gray-500">加载中...</div>
    
    <div v-else-if="conversations.length === 0" class="text-center py-20 text-gray-400 bg-white rounded-xl border border-gray-100">
      还没有消息哦
    </div>
    
    <div v-else class="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
      <div 
        v-for="conv in conversations" 
        :key="conv.user.id"
        class="p-4 flex items-center gap-4 hover:bg-gray-50 cursor-pointer transition-colors"
        @click="goToChat(conv.user.id)"
      >
        <div class="relative">
          <img 
            :src="getImageUrl(conv.user.avatar_url) || 'https://via.placeholder.com/50'" 
            class="w-12 h-12 rounded-full object-cover border border-gray-200"
          >
          <div v-if="conv.unread_count > 0" class="absolute -top-1 -right-1 w-5 h-5 bg-xhs-red text-white text-xs flex items-center justify-center rounded-full border-2 border-white">
            {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
          </div>
        </div>
        
        <div class="flex-1 min-w-0">
          <div class="flex justify-between items-baseline mb-1">
            <h3 class="font-medium text-gray-900 truncate">{{ conv.user.nickname }}</h3>
            <span class="text-xs text-gray-400 flex-shrink-0">{{ formatTime(conv.timestamp) }}</span>
          </div>
          <p class="text-sm text-gray-500 truncate">{{ conv.last_message.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

