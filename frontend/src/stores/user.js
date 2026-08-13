import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getCurrentUser, refreshToken, logout as apiLogout } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refresh = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => userInfo.value?.role || '')

  async function loginAction(credentials) {
    loading.value = true
    try {
      const res = await login(credentials)
      token.value = res.data.access
      refresh.value = res.data.refresh
      userInfo.value = res.data.user
      localStorage.setItem('access_token', res.data.access)
      localStorage.setItem('refresh_token', res.data.refresh)
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchUserInfo() {
    const res = await getCurrentUser()
    userInfo.value = res.data
    return res.data
  }

  async function refreshTokenAction() {
    try {
      const res = await refreshToken({ refresh: refresh.value })
      token.value = res.data.access
      refresh.value = res.data.refresh
      localStorage.setItem('access_token', res.data.access)
      localStorage.setItem('refresh_token', res.data.refresh)
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout() {
    token.value = ''
    refresh.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  function hasRole(...roles) {
    if (role.value === 'super_admin') return true
    return roles.includes(role.value)
  }

  return {
    token,
    refresh,
    userInfo,
    loading,
    isLoggedIn,
    role,
    loginAction,
    fetchUserInfo,
    refreshTokenAction,
    logout,
    hasRole,
  }
})
