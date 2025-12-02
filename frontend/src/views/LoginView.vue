<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'
import { login, register } from '../api'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const isLogin = ref(true)
const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: '',
  nickname: ''
})

const handleSubmit = async () => {
  try {
    if (isLogin.value) {
      const res = await login(form.value.username, form.value.password)
      if (res.data.success) {
        userStore.login(res.data.user)
        ElMessage.success('登录成功')
        router.push('/')
      } else {
        ElMessage.error(res.data.message)
      }
    } else {
      const res = await register(form.value.username, form.value.password, form.value.nickname)
      if (res.data.success) {
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
      } else {
        ElMessage.error(res.data.message)
      }
    }
  } catch (e) {
    ElMessage.error('操作失败，请检查网络')
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-80px)]">
    <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 w-full max-w-md">
      <h2 class="text-2xl font-bold text-center mb-8 text-gray-800">{{ isLogin ? '登录小红书' : '注册账号' }}</h2>
      
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <input v-model="form.username" type="text" placeholder="用户名" class="w-full h-12 px-4 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-colors" required>
        </div>
        <div>
          <input v-model="form.password" type="password" placeholder="密码" class="w-full h-12 px-4 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-colors" required>
        </div>
        <div v-if="!isLogin">
          <input v-model="form.nickname" type="text" placeholder="昵称 (可选)" class="w-full h-12 px-4 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-colors">
        </div>
        
        <button type="submit" class="w-full h-12 bg-xhs-red text-white rounded-full font-bold hover:bg-red-600 transition-colors shadow-md shadow-red-100">
          {{ isLogin ? '登录' : '注册' }}
        </button>
      </form>
      
      <div class="mt-6 text-center text-sm text-gray-500">
        {{ isLogin ? '还没有账号？' : '已有账号？' }}
        <button @click="isLogin = !isLogin" class="text-xhs-red font-medium hover:underline">
          {{ isLogin ? '去注册' : '去登录' }}
        </button>
      </div>
    </div>
  </div>
</template>










