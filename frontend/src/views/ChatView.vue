<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getConversation, sendMessage, markMessagesRead, getPublicUserProfile, getImageUrl } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const targetUser = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const messagesContainer = ref(null)
const pollingInterval = ref(null)

const targetUserId = route.params.id

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const fetchMessages = async () => {
  if (!userStore.user) return
  try {
    const res = await getConversation(targetUserId, userStore.user.id)
    // If new messages arrived, update and scroll
    if (res.data.messages.length !== messages.value.length || (messages.value.length > 0 && res.data.messages[res.data.messages.length-1].id !== messages.value[messages.value.length-1].id)) {
        messages.value = res.data.messages
        scrollToBottom()
        // Mark as read if last message is from them
        if (messages.value.length > 0) {
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg.sender_id == targetUserId && !lastMsg.is_read) {
                 await markMessagesRead(userStore.user.id, targetUserId)
            }
        }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchTargetUser = async () => {
  try {
    const res = await getPublicUserProfile(targetUserId)
    targetUser.value = res.data.user
  } catch (e) {
    ElMessage.error('用户不存在')
    router.push('/messages')
  }
}

const handleSend = async () => {
  if (!newMessage.value.trim()) return
  
  try {
    const content = newMessage.value
    newMessage.value = '' // Optimistic clear
    
    const res = await sendMessage(userStore.user.id, targetUserId, content)
    if (res.data.success) {
      await fetchMessages()
    } else {
      ElMessage.error(res.data.message || '发送失败')
      newMessage.value = content // Restore on fail
    }
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

onMounted(async () => {
  if (!userStore.user) {
      router.push('/login')
      return
  }
  await fetchTargetUser()
  await fetchMessages()
  
  // Simple polling for new messages every 3 seconds
  pollingInterval.value = setInterval(fetchMessages, 3000)
})

onUnmounted(() => {
  if (pollingInterval.value) clearInterval(pollingInterval.value)
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-3.5rem)] bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 flex-shrink-0">
      <button @click="router.back()" class="text-gray-500 hover:text-gray-700">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
        </svg>
      </button>
      <div v-if="targetUser" class="flex items-center gap-2 cursor-pointer" @click="router.push(`/user/${targetUser.id}`)">
        <img :src="getImageUrl(targetUser.avatar_url) || 'https://via.placeholder.com/40'" class="w-8 h-8 rounded-full object-cover">
        <span class="font-medium text-gray-900">{{ targetUser.nickname }}</span>
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
      <div v-if="loading" class="text-center text-gray-400 text-sm py-4">加载中...</div>
      
      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="flex gap-3"
        :class="msg.sender_id === userStore.user.id ? 'flex-row-reverse' : ''"
      >
        <img 
            :src="getImageUrl(msg.sender_id === userStore.user.id ? userStore.user.avatar_url : targetUser?.avatar_url) || 'https://via.placeholder.com/40'" 
            class="w-9 h-9 rounded-full object-cover flex-shrink-0 bg-white border border-gray-100"
        >
        
        <div 
          class="max-w-[70%] px-4 py-2.5 rounded-2xl text-sm break-words"
          :class="msg.sender_id === userStore.user.id 
            ? 'bg-xhs-red text-white rounded-tr-none' 
            : 'bg-white text-gray-800 border border-gray-100 rounded-tl-none'"
        >
          {{ msg.content }}
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="bg-white border-t border-gray-200 p-4 flex-shrink-0">
      <div class="flex gap-3 max-w-4xl mx-auto">
        <input 
          v-model="newMessage"
          type="text" 
          class="flex-1 bg-gray-100 rounded-full px-4 py-2.5 text-sm focus:bg-white focus:ring-1 focus:ring-xhs-red focus:outline-none transition-all"
          placeholder="发私信..."
          @keyup.enter="handleSend"
        >
        <button 
          @click="handleSend"
          class="bg-xhs-red text-white px-5 py-2 rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          :disabled="!newMessage.trim()"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

