import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 0) {
      return res
    }
    if (res.code === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
      return Promise.reject(new Error(res.message || '未授权'))
    }
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message))
  },
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    }
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else if (error.message !== 'canceled') {
      ElMessage.error('网络请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
