<script setup>
import { ref } from 'vue'
import { createPost } from '../api'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const fileInput = ref(null)
const previewUrl = ref('')
const file = ref(null)

const categories = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]

const form = ref({
  title: '',
  content: '',
  category: '推荐'
})

const handleFileChange = (e) => {
  const selectedFile = e.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    previewUrl.value = URL.createObjectURL(selectedFile)
  }
}

const triggerUpload = () => {
  fileInput.value.click()
}

const handleSubmit = async () => {
  if (!file.value) {
    ElMessage.warning('请上传图片')
    return
  }
  
  const formData = new FormData()
  formData.append('user_id', userStore.user.id)
  formData.append('title', form.value.title)
  formData.append('content', form.value.content)
  formData.append('category', form.value.category)
  formData.append('image', file.value)
  
  try {
    const res = await createPost(formData)
    if (res.data.success) {
      ElMessage.success('发布成功')
      router.push('/')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('发布失败')
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-6 flex gap-8">
    <!-- Left: Image Upload -->
    <div class="w-1/3">
      <div 
        class="aspect-[3/4] bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center cursor-pointer hover:border-xhs-red hover:bg-red-50 transition-all overflow-hidden relative group"
        @click="triggerUpload"
      >
        <img v-if="previewUrl" :src="previewUrl" class="absolute inset-0 w-full h-full object-cover">
        <div v-else class="text-center p-4 text-gray-400 group-hover:text-xhs-red">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 mx-auto mb-2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
          </svg>
          <span class="text-sm font-medium">点击上传封面</span>
        </div>
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange">
      </div>
    </div>

    <!-- Right: Form -->
    <div class="flex-1 space-y-6">
      <input 
        v-model="form.title" 
        type="text" 
        placeholder="填写标题会有更多人赞哦~" 
        class="w-full text-xl font-bold border-b border-gray-200 py-2 focus:border-xhs-red focus:outline-none transition-colors placeholder-gray-300"
      >
      
      <textarea 
        v-model="form.content" 
        placeholder="填写更全面的描述信息，让更多人看到你吧！" 
        class="w-full h-40 resize-none text-gray-600 focus:outline-none placeholder-gray-300"
      ></textarea>
      
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">选择分类</label>
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="cat in categories" 
            :key="cat"
            type="button"
            @click="form.category = cat"
            class="px-3 py-1 text-xs rounded-full border transition-all"
            :class="form.category === cat ? 'border-xhs-red text-xhs-red bg-red-50' : 'border-gray-200 text-gray-500 hover:border-gray-300'"
          >
            {{ cat }}
          </button>
        </div>
      </div>
      
      <div class="pt-4">
        <button @click="handleSubmit" class="w-32 h-10 bg-xhs-red text-white rounded-full font-medium hover:bg-red-600 transition-colors">
          发布笔记
        </button>
      </div>
    </div>
  </div>
</template>




