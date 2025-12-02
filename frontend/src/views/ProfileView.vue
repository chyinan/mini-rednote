<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useTransitionStore } from '../stores/transition'
import { getUserPosts, getUserLikedPosts, getUserCollectedPosts, updateProfile, getImageUrl, deletePost, updatePostVisibility, getPublicUserProfile, followUser, unfollowUser, checkIsFollowing, getFollowers, getFollowing, getFollowCounts } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import WaterfallCard from '../components/WaterfallCard.vue'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const transitionStore = useTransitionStore()
const user = ref(null)
const posts = ref([])
const likedPosts = ref([])
const collectedPosts = ref([])
const activeTab = ref('notes') // 'notes', 'collect', 'likes'
const isEditing = ref(false)
const fileInput = ref(null)
const editForm = ref({
  nickname: '',
  avatar: null,
  avatarPreview: ''
})

// Follow related state
const followCounts = ref({ followers: 0, following: 0 })
const isFollowing = ref(false)
const showFollowList = ref(false)
const followListType = ref('followers') // 'followers' or 'following'
const followList = ref([])

// Column Management
const columnCount = ref(2)
const updateColumnCount = () => {
  const width = window.innerWidth
  if (width >= 1280) columnCount.value = 5 // xl (not used in profile usually, but good to align)
  else if (width >= 1024) columnCount.value = 4 // lg
  else if (width >= 768) columnCount.value = 3 // md
  else columnCount.value = 2 // default
}

// Helper to compute waterfall for any list
const getWaterfall = (list) => {
  if (!list || !list.length) return []
  const cols = Array.from({ length: columnCount.value }, () => [])
  list.forEach((item, index) => {
    cols[index % columnCount.value].push(item)
  })
  return cols
}

const waterfallPosts = computed(() => getWaterfall(posts.value).filter(col => col.length > 0))
const waterfallLiked = computed(() => getWaterfall(likedPosts.value).filter(col => col.length > 0))
const waterfallCollected = computed(() => getWaterfall(collectedPosts.value).filter(col => col.length > 0))

const colWidthStyle = computed(() => ({
  width: `calc((100% - ${(columnCount.value - 1)} * 1rem) / ${columnCount.value})`
}))

// Check if viewing own profile
const isOwnProfile = computed(() => {
  return userStore.user && user.value && userStore.user.id === user.value.id
})

const fetchUserContent = async () => {
  if (!user.value) return
  
  // Fetch follow counts
  try {
    const res = await getFollowCounts(user.value.id)
    followCounts.value = res.data.counts
  } catch (e) {
    console.error('Error fetching follow counts', e)
  }

  // Check follow status if not own profile
  if (!isOwnProfile.value && userStore.user) {
    try {
      const res = await checkIsFollowing(user.value.id, userStore.user.id)
      isFollowing.value = res.data.is_following
    } catch (e) {
      console.error(e)
    }
  }

  console.log('Fetching content for tab:', activeTab.value)
  try {
    if (activeTab.value === 'notes') {
      // Pass current user ID to see private posts if owner
      const currentUserId = userStore.user ? userStore.user.id : null
      const res = await getUserPosts(user.value.id, currentUserId)
      posts.value = res.data
    } else if (activeTab.value === 'likes') {
      const res = await getUserLikedPosts(user.value.id)
      likedPosts.value = res.data
    } else if (activeTab.value === 'collect') {
      const res = await getUserCollectedPosts(user.value.id)
      collectedPosts.value = res.data
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('获取数据失败')
  }
}

const loadUser = async () => {
  const routeId = route.params.id
  if (routeId) {
    try {
      const res = await getPublicUserProfile(routeId)
      user.value = res.data.user
    } catch (e) {
      ElMessage.error('用户不存在')
      router.push('/')
      return
    }
  } else {
    user.value = userStore.user
    if (!user.value) {
       router.push('/login')
       return
    }
  }
  fetchUserContent()
}

watch(() => route.params.id, () => {
  activeTab.value = 'notes'
  loadUser()
})

watch(activeTab, () => {
  fetchUserContent()
})

onMounted(() => {
  loadUser()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount)
})

const startEdit = () => {
  if (!isOwnProfile.value) return
  editForm.value.nickname = user.value.nickname
  editForm.value.avatarPreview = getImageUrl(user.value.avatar_url)
  isEditing.value = true
}

const triggerAvatarUpload = () => {
  fileInput.value.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    editForm.value.avatar = file
    editForm.value.avatarPreview = URL.createObjectURL(file)
  }
}

const saveProfile = async () => {
  const formData = new FormData()
  formData.append('user_id', user.value.id)
  formData.append('nickname', editForm.value.nickname)
  if (editForm.value.avatar) {
    formData.append('avatar', editForm.value.avatar)
  }

  try {
    const res = await updateProfile(formData)
    if (res.data.success) {
      userStore.login(res.data.user)
      user.value = res.data.user
      isEditing.value = false
      ElMessage.success('保存成功')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const goToDetail = (id, event) => {
  const cardElement = event?.currentTarget
  const imgElement = cardElement?.querySelector('img')
  
  if (imgElement) {
    const rect = imgElement.getBoundingClientRect()
    transitionStore.setRect(rect)
  }
  
  // Append to current path instead of absolute /explore
  // Check if we are already in a nested route to avoid double stacking (though unlikely with replacement)
  // Actually, we want to append 'explore/:id' to the current path
  // But router.push works best with absolute paths or relative.
  // If current is /user/123, we want /user/123/explore/456
  // If current is /profile, we want /profile/explore/456
  
  // Simply using 'explore/${id}' (relative) should work if the current route is a parent
  // But we need to be careful.
  
  // Let's use the resolved path logic to be safe, or just append to current route.path
  // Ensure no trailing slash issues
  const currentPath = route.path.endsWith('/') ? route.path : route.path + '/'
  router.push(`${currentPath}explore/${id}`)
}

const handleDeletePost = async (postId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条笔记吗？此操作无法撤销。', '提示', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await deletePost(postId, userStore.user.id)
    if (res.data.success) {
      ElMessage.success('删除成功')
      fetchUserContent()
    } else {
      ElMessage.error(res.data.message || '删除失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('操作失败')
    }
  }
}

const handleTogglePrivacy = async (postId, newStatus) => {
  try {
    const res = await updatePostVisibility(postId, userStore.user.id, newStatus)
    if (res.data.success) {
      ElMessage.success(newStatus ? '已设为仅自己可见' : '已设为公开')
      const post = posts.value.find(p => p.id === postId)
      if (post) {
        post.is_private = newStatus
      }
    } else {
      ElMessage.error(res.data.message || '操作失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('操作失败')
  }
}

const handleFollow = async () => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    const res = await followUser(user.value.id, userStore.user.id)
    if (res.data.success) {
      isFollowing.value = true
      followCounts.value.followers++ // Optimistic update
      ElMessage.success('关注成功')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('关注失败')
  }
}

const handleUnfollow = async () => {
  try {
    const res = await unfollowUser(user.value.id, userStore.user.id)
    if (res.data.success) {
      isFollowing.value = false
      followCounts.value.followers-- // Optimistic update
      ElMessage.success('已取消关注')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('取消关注失败')
  }
}

const openFollowList = async (type) => {
  followListType.value = type
  showFollowList.value = true
  followList.value = [] // Clear first
  
  try {
    const res = type === 'followers' 
      ? await getFollowers(user.value.id)
      : await getFollowing(user.value.id)
    
    // Response format: { success: true, followers: [...] } or { success: true, following: [...] }
    followList.value = type === 'followers' ? res.data.followers : res.data.following
  } catch (e) {
    console.error(e)
    ElMessage.error('获取列表失败')
  }
}

const goToUser = (userId) => {
  showFollowList.value = false
  router.push(`/user/${userId}`)
}

const goToChat = () => {
  if (user.value) {
    router.push(`/messages/${user.value.id}`)
  }
}
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-5xl" v-if="user">
    <!-- Profile Header -->
    <div class="flex flex-col items-center mb-12">
      <div class="relative group cursor-pointer" @click="isOwnProfile && startEdit()">
        <img 
          :src="getImageUrl(user.avatar_url) || 'https://via.placeholder.com/100'" 
          class="w-24 h-24 rounded-full object-cover border-2 border-gray-100"
        >
        <div v-if="isOwnProfile" class="absolute inset-0 bg-black/30 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <span class="text-white text-xs font-medium">编辑</span>
        </div>
      </div>
      <h1 class="mt-4 text-xl font-bold text-gray-900">{{ user.nickname }}</h1>
      <p class="text-gray-500 text-sm mt-1">小红书号: {{ user.username }}</p>
      
      <!-- Follow Counts -->
      <div class="flex gap-6 mt-3 text-sm">
        <div class="cursor-pointer hover:text-xhs-red" @click="openFollowList('following')">
          <span class="font-bold text-gray-900">{{ followCounts.following }}</span>
          <span class="text-gray-500 ml-1">关注</span>
        </div>
        <div class="cursor-pointer hover:text-xhs-red" @click="openFollowList('followers')">
          <span class="font-bold text-gray-900">{{ followCounts.followers }}</span>
          <span class="text-gray-500 ml-1">粉丝</span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div v-if="isOwnProfile" class="mt-4">
        <button @click="startEdit" class="px-6 py-1.5 border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-gray-400 transition-colors">
          编辑资料
        </button>
      </div>
      <div v-else class="mt-4 flex gap-2">
        <button 
          v-if="isFollowing" 
          @click="handleUnfollow" 
          class="px-6 py-1.5 border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-gray-400 transition-colors"
        >
          已关注
        </button>
        <button 
          v-else 
          @click="handleFollow" 
          class="px-6 py-1.5 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600 transition-colors"
        >
          关注
        </button>
        <button @click="goToChat" class="px-6 py-1.5 border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-gray-400 transition-colors">
          发私信
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex justify-center gap-8 border-b border-gray-100 mb-6">
      <button 
        @click="activeTab = 'notes'"
        class="pb-3 px-2 text-sm font-medium transition-colors relative"
        :class="activeTab === 'notes' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
      >
        笔记
        <div v-if="activeTab === 'notes'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-xhs-red rounded-full"></div>
      </button>
      <button 
        @click="activeTab = 'collect'"
        class="pb-3 px-2 text-sm font-medium transition-colors relative"
        :class="activeTab === 'collect' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
      >
        收藏
        <div v-if="activeTab === 'collect'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-xhs-red rounded-full"></div>
      </button>
      <button 
        @click="activeTab = 'likes'"
        class="pb-3 px-2 text-sm font-medium transition-colors relative"
        :class="activeTab === 'likes' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
      >
        点赞
        <div v-if="activeTab === 'likes'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-xhs-red rounded-full"></div>
      </button>
    </div>

    <!-- Content -->
    <div v-if="activeTab === 'notes'">
      <!-- JS Calculated Columns -->
      <div class="flex gap-4 items-start" :class="{ 'justify-center': posts.length < columnCount }">
        <div v-for="(col, index) in waterfallPosts" :key="index" 
             class="space-y-4 flex flex-col"
             :class="posts.length < columnCount ? 'flex-none' : 'flex-1'"
             :style="posts.length < columnCount ? colWidthStyle : {}"
        >
          <WaterfallCard 
            v-for="post in col" 
            :key="post.id" 
            :post="{ ...post, nickname: user.nickname, avatar_url: user.avatar_url }" 
            :show-actions="isOwnProfile"
            @click="goToDetail"
            @delete="handleDeletePost"
            @toggle-privacy="handleTogglePrivacy"
          />
        </div>
      </div>
      <div v-if="posts.length === 0" class="text-center py-20 text-gray-400">
        还没有发布过笔记哦
      </div>
    </div>

    <div v-else-if="activeTab === 'likes'">
      <div class="flex gap-4 items-start" :class="{ 'justify-center': likedPosts.length < columnCount }">
        <div v-for="(col, index) in waterfallLiked" :key="index" 
             class="space-y-4 flex flex-col"
             :class="likedPosts.length < columnCount ? 'flex-none' : 'flex-1'"
             :style="likedPosts.length < columnCount ? colWidthStyle : {}"
        >
          <WaterfallCard 
            v-for="post in col" 
            :key="post.id" 
            :post="post" 
            @click="goToDetail"
          />
        </div>
      </div>
      <div v-if="likedPosts.length === 0" class="text-center py-20 text-gray-400">
        还没有点赞过笔记哦
      </div>
    </div>
    
    <div v-else-if="activeTab === 'collect'">
      <div class="flex gap-4 items-start" :class="{ 'justify-center': collectedPosts.length < columnCount }">
        <div v-for="(col, index) in waterfallCollected" :key="index" 
             class="space-y-4 flex flex-col"
             :class="collectedPosts.length < columnCount ? 'flex-none' : 'flex-1'"
             :style="collectedPosts.length < columnCount ? colWidthStyle : {}"
        >
          <WaterfallCard 
            v-for="post in col" 
            :key="post.id" 
            :post="post" 
            @click="goToDetail"
          />
        </div>
      </div>
      <div v-if="collectedPosts.length === 0" class="text-center py-20 text-gray-400">
        还没有收藏过笔记哦
      </div>
    </div>

    <!-- Follow List Modal -->
    <div v-if="showFollowList" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showFollowList = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md h-[500px] flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">{{ followListType === 'followers' ? '粉丝列表' : '关注列表' }}</h3>
          <button @click="showFollowList = false" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto">
          <div v-if="followList.length === 0" class="text-center py-10 text-gray-400">
            暂无{{ followListType === 'followers' ? '粉丝' : '关注' }}
          </div>
          <div v-else class="space-y-4">
            <div v-for="item in followList" :key="item.id" class="flex items-center justify-between">
              <div class="flex items-center gap-3 cursor-pointer" @click="goToUser(item.id)">
                <img :src="getImageUrl(item.avatar_url) || 'https://via.placeholder.com/40'" class="w-10 h-10 rounded-full object-cover bg-gray-100">
                <span class="font-medium text-gray-900">{{ item.nickname }}</span>
              </div>
              <!-- Could add follow/unfollow buttons here for quick action -->
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <div v-if="isEditing" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="isEditing = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h3 class="text-lg font-bold text-center mb-6">编辑资料</h3>
        
        <div class="flex flex-col items-center mb-6">
          <div class="relative cursor-pointer" @click="triggerAvatarUpload">
            <img :src="editForm.avatarPreview || 'https://via.placeholder.com/100'" class="w-20 h-20 rounded-full object-cover border border-gray-100">
            <div class="absolute bottom-0 right-0 bg-gray-800 text-white p-1.5 rounded-full border-2 border-white">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3">
                <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
              </svg>
            </div>
          </div>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange">
          <p class="text-xs text-gray-400 mt-2">点击更换头像</p>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">昵称</label>
            <input v-model="editForm.nickname" type="text" class="w-full h-10 px-3 bg-gray-50 rounded-lg border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none text-sm">
          </div>
        </div>

        <div class="flex gap-3 mt-8">
          <button @click="isEditing = false" class="flex-1 h-10 rounded-full border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50">取消</button>
          <button @click="saveProfile" class="flex-1 h-10 rounded-full bg-xhs-red text-white text-sm font-medium hover:bg-red-600">保存</button>
        </div>
      </div>
    </div>

    <!-- Nested Router View for Post Detail -->
    <router-view v-slot="{ Component }">
      <transition name="modal-fade">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style>
/* Reuse modal transition styles from HomeView if needed, or define here */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
