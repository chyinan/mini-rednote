import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useTransitionStore = defineStore('transition', () => {
  const selectedImgRect = ref(null)

  const setRect = (rect) => {
    selectedImgRect.value = rect
  }

  return { selectedImgRect, setRect }
})


