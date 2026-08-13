<template>
  <el-container class="register-container">
    <div class="register-bg"></div>
    <div class="register-card">
      <div class="register-header">
        <h1>注册新账号</h1>
        <p>加入智慧灌区管理系统</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="register-form" @submit.prevent="handleRegister">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="real_name">
              <el-input v-model="form.real_name" placeholder="真实姓名" :prefix-icon="UserFilled" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码(至少8位)" :prefix-icon="Lock" show-password />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="confirm_password">
              <el-input v-model="form.confirm_password" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="phone">
              <el-input v-model="form.phone" placeholder="手机号(选填)" :prefix-icon="Phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="邮箱(选填)" :prefix-icon="Message" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="department">
              <el-input v-model="form.department" placeholder="部门(选填)" :prefix-icon="OfficeBuilding" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="position">
              <el-input v-model="form.position" placeholder="职位(选填)" :prefix-icon="Postcard" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" class="register-btn" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="link">立即登录</router-link>
      </div>
    </div>
  </el-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, UserFilled, Lock, Phone, Message, OfficeBuilding, Postcard } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { register } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  username: '',
  real_name: '',
  password: '',
  confirm_password: '',
  phone: '',
  email: '',
  department: '',
  position: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度 3-32 位', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少 8 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await register({
      username: form.username,
      password: form.password,
      real_name: form.real_name,
      phone: form.phone,
      email: form.email,
      department: form.department,
      position: form.position,
    })
    userStore.token = res.data.access
    userStore.refresh = res.data.refresh
    userStore.userInfo = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)

    ElMessage.success('注册成功，欢迎加入！')
    router.push('/dashboard')
  } catch (e) {
    console.error('Register failed:', e)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.register-bg {
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

.register-card {
  position: relative;
  width: 640px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px 44px 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-header {
  text-align: center;
  margin-bottom: 28px;

  h1 {
    font-size: 24px;
    font-weight: 700;
    color: #1e3c72;
    margin-bottom: 6px;
  }

  p {
    font-size: 13px;
    color: #909399;
    letter-spacing: 1px;
  }
}

.register-form {
  :deep(.el-input__wrapper) {
    border-radius: 8px;
  }

  .register-btn {
    width: 100%;
    height: 44px;
    font-size: 15px;
    border-radius: 8px;
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
    border: none;
  }
}

.register-footer {
  text-align: center;
  margin-top: 12px;
  color: #909399;
  font-size: 13px;

  .link {
    color: #409eff;
    text-decoration: none;
    margin-left: 6px;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
