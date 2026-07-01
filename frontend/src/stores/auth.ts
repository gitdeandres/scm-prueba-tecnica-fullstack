import client from '@/api/client'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(sessionStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const response = await client.post('/auth/login', { username, password })
    token.value = response.data.access_token
    sessionStorage.setItem('access_token', token.value!)
  }

  function logout() {
    token.value = null
    sessionStorage.removeItem('access_token')
  }

  return { token, isAuthenticated, login, logout }
})
