import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '工作台' } },

      { path: 'inspection/list', name: 'InspectionList', component: () => import('@/views/inspection/InspectionList.vue'), meta: { title: '巡检管理' } },
      { path: 'inspection/workorders', name: 'WorkOrderList', component: () => import('@/views/inspection/WorkOrderList.vue'), meta: { title: '工单管理' } },

      { path: 'water/stations', name: 'MeasureStations', component: () => import('@/views/water/MeasureStations.vue'), meta: { title: '量测水测站' } },
      { path: 'water/data', name: 'WaterData', component: () => import('@/views/water/WaterData.vue'), meta: { title: '量测水数据' } },
      { path: 'water/alarms', name: 'WaterAlarms', component: () => import('@/views/water/WaterAlarms.vue'), meta: { title: '水量告警' } },

      { path: 'irrigation/devices', name: 'IrrigationDevices', component: () => import('@/views/irrigation/IrrigationDevices.vue'), meta: { title: '灌溉设备' } },
      { path: 'irrigation/plans', name: 'IrrigationPlans', component: () => import('@/views/irrigation/IrrigationPlans.vue'), meta: { title: '灌溉计划' } },
      { path: 'irrigation/records', name: 'IrrigationRecords', component: () => import('@/views/irrigation/IrrigationRecords.vue'), meta: { title: '灌溉记录' } },

      { path: 'allocation/sources', name: 'WaterSources', component: () => import('@/views/allocation/WaterSources.vue'), meta: { title: '水源管理' } },
      { path: 'allocation/plans', name: 'AllocationPlans', component: () => import('@/views/allocation/AllocationPlans.vue'), meta: { title: '分配方案' } },
      { path: 'allocation/transfers', name: 'WaterTransfers', component: () => import('@/views/allocation/WaterTransfers.vue'), meta: { title: '调水调度' } },

      { path: 'price/policies', name: 'PricePolicies', component: () => import('@/views/price/PricePolicies.vue'), meta: { title: '水价政策' } },
      { path: 'price/users', name: 'PriceUsers', component: () => import('@/views/price/PriceUsers.vue'), meta: { title: '用水户' } },
      { path: 'price/bills', name: 'PriceBills', component: () => import('@/views/price/PriceBills.vue'), meta: { title: '水费账单' } },

      { path: 'daily/notices', name: 'Notices', component: () => import('@/views/daily/Notices.vue'), meta: { title: '通知公告' } },
      { path: 'daily/meetings', name: 'Meetings', component: () => import('@/views/daily/Meetings.vue'), meta: { title: '会议管理' } },
      { path: 'daily/assets', name: 'Assets', component: () => import('@/views/daily/Assets.vue'), meta: { title: '固定资产' } },
      { path: 'daily/documents', name: 'Documents', component: () => import('@/views/daily/Documents.vue'), meta: { title: '文档资料' } },

      { path: 'soil/stations', name: 'SoilStations', component: () => import('@/views/soil/SoilStations.vue'), meta: { title: '墒情气象测站' } },
      { path: 'soil/data', name: 'SoilData', component: () => import('@/views/soil/SoilData.vue'), meta: { title: '墒情数据' } },
      { path: 'soil/weather', name: 'WeatherData', component: () => import('@/views/soil/WeatherData.vue'), meta: { title: '气象数据' } },
      { path: 'soil/forecasts', name: 'SoilForecasts', component: () => import('@/views/soil/SoilForecasts.vue'), meta: { title: '墒情预报' } },

      { path: 'system/users', name: 'SystemUsers', component: () => import('@/views/system/Users.vue'), meta: { title: '用户管理', roles: ['admin', 'super_admin'] } },
      { path: 'system/logs', name: 'SystemLogs', component: () => import('@/views/system/Logs.vue'), meta: { title: '操作日志' } },
      { path: 'system/configs', name: 'SystemConfigs', component: () => import('@/views/system/Configs.vue'), meta: { title: '系统配置' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

NProgress.configure({ showSpinner: false })

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - 灌区管理系统` : '灌区管理系统'

  const userStore = useUserStore()

  if (to.meta.public) {
    if (userStore.isLoggedIn && to.name === 'Login') {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  if (!userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      userStore.logout()
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }

  if (to.meta.roles && !userStore.hasRole(...to.meta.roles)) {
    next('/dashboard')
    return
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
