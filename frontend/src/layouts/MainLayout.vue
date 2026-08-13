<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-area">
        <el-icon :size="28" color="#409eff"><WaterDrop /></el-icon>
        <span v-if="!isCollapse" class="logo-text">灌区管理系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>

        <el-sub-menu index="inspection">
          <template #title>
            <el-icon><Tickets /></el-icon>
            <span>巡检与工单</span>
          </template>
          <el-menu-item index="/inspection/list">巡检管理</el-menu-item>
          <el-menu-item index="/inspection/workorders">工单管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="water">
          <template #title>
            <el-icon><DataLine /></el-icon>
            <span>量测水管理</span>
          </template>
          <el-menu-item index="/water/stations">测站管理</el-menu-item>
          <el-menu-item index="/water/data">量测数据</el-menu-item>
          <el-menu-item index="/water/alarms">水量告警</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="irrigation">
          <template #title>
            <el-icon><Aim /></el-icon>
            <span>智慧灌排</span>
          </template>
          <el-menu-item index="/irrigation/devices">灌溉设备</el-menu-item>
          <el-menu-item index="/irrigation/plans">灌溉计划</el-menu-item>
          <el-menu-item index="/irrigation/records">灌溉记录</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="allocation">
          <template #title>
            <el-icon><Share /></el-icon>
            <span>水资源分配</span>
          </template>
          <el-menu-item index="/allocation/sources">水源管理</el-menu-item>
          <el-menu-item index="/allocation/plans">分配方案</el-menu-item>
          <el-menu-item index="/allocation/transfers">调水调度</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="price">
          <template #title>
            <el-icon><Money /></el-icon>
            <span>水价改革</span>
          </template>
          <el-menu-item index="/price/policies">水价政策</el-menu-item>
          <el-menu-item index="/price/users">用水户</el-menu-item>
          <el-menu-item index="/price/bills">水费账单</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="daily">
          <template #title>
            <el-icon><Calendar /></el-icon>
            <span>日常管理</span>
          </template>
          <el-menu-item index="/daily/notices">通知公告</el-menu-item>
          <el-menu-item index="/daily/meetings">会议管理</el-menu-item>
          <el-menu-item index="/daily/assets">固定资产</el-menu-item>
          <el-menu-item index="/daily/documents">文档资料</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="soil">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>墒情气象</span>
          </template>
          <el-menu-item index="/soil/stations">测站管理</el-menu-item>
          <el-menu-item index="/soil/data">墒情数据</el-menu-item>
          <el-menu-item index="/soil/weather">气象数据</el-menu-item>
          <el-menu-item index="/soil/forecasts">墒情预报</el-menu-item>
        </el-sub-menu>

        <el-sub-menu v-if="userStore.hasRole('admin', 'super_admin')" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/logs">操作日志</el-menu-item>
          <el-menu-item index="/system/configs">系统配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon :size="20" class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="刷新" placement="bottom">
            <el-icon class="header-icon" @click="refreshPage"><Refresh /></el-icon>
          </el-tooltip>
          <el-tooltip content="全屏" placement="bottom">
            <el-icon class="header-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
          </el-tooltip>
          <el-dropdown trigger="click" @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.real_name?.[0] || userStore.userInfo?.username?.[0]?.toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
              <el-tag size="small" type="info">{{ userStore.userInfo?.role_display }}</el-tag>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <AiAssistant />
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Pouring, Odometer, Tickets, DataLine, Aim, Share, Money, Calendar, Monitor, Setting,
  Fold, Expand, Refresh, FullScreen, User, Lock, SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { changePassword, logout as apiLogout } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

function refreshPage() {
  router.go(0)
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

async function handleUserCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
      await apiLogout({ refresh: userStore.refresh })
      userStore.logout()
      router.push('/login')
    } catch {}
  } else if (command === 'password') {
    showPasswordDialog()
  }
}

function showPasswordDialog() {
  ElMessageBox.prompt('请输入新密码', '修改密码', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputType: 'password',
    inputPattern: /^.{8,}$/,
    inputErrorMessage: '密码长度不少于8位',
  }).then(async ({ value }) => {
    const oldPwd = await ElMessageBox.prompt('请输入原密码', '验证', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'password',
    })
    await changePassword({ old_password: oldPwd.value, new_password: value })
    ElMessage.success('密码修改成功')
  }).catch(() => {})
}
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  .logo-text {
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    white-space: nowrap;
  }
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.15) !important;
}

.header {
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.06);
  height: 60px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .collapse-btn {
    cursor: pointer;
    color: #606266;

    &:hover {
      color: #409eff;
    }
  }

  .header-icon {
    font-size: 18px;
    color: #606266;
    cursor: pointer;

    &:hover {
      color: #409eff;
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 20px;
    transition: background 0.2s;

    &:hover {
      background: #f5f7fa;
    }

    .user-name {
      font-size: 14px;
      color: #303133;
    }
  }
}

.main-content {
  background: #f0f2f5;
  padding: 0;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
