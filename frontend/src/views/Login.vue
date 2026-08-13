<template>
  <el-container class="login-container">
    <div class="login-bg"></div>
    <div class="login-card">
      <div class="login-header">
        <h1>灌区管理系统</h1>
        <p>Smart Irrigation Management System</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="login-form" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>© 2026 灌区管理系统</span>
        <span class="divider">|</span>
        <router-link to="/register" class="link">注册新账号</router-link>
      </div>
    </div>
  </el-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.loginAction(form)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (e) {
    console.error('Login failed:', e)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #409eff 100%);

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 20% 30%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(255,255,255,0.1) 0%, transparent 50%);
  }
}

.login-card {
  position: relative;
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 48px 40px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;

  h1 {
    font-size: 28px;
    font-weight: 700;
    color: #1e3c72;
    margin-bottom: 8px;
  }

  p {
    font-size: 14px;
    color: #909399;
    letter-spacing: 1px;
  }
}

.login-form {
  .el-input {
    height: 46px;
  }

  :deep(.el-input__wrapper) {
    border-radius: 8px;
  }

  .login-btn {
    width: 100%;
    height: 46px;
    font-size: 16px;
    border-radius: 8px;
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
    border: none;
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: #c0c4cc;
  font-size: 12px;

  .divider {
    margin: 0 8px;
  }

  .link {
    color: #409eff;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
