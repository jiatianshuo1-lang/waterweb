<template>
  <GenericList title="用户管理" :apiList="getUserList" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getUserList } from '@/api'

const columns = [
  { prop: 'username', label: '用户名', width: 120 },
  { prop: 'real_name', label: '姓名', width: 120 },
  { prop: 'role_display', label: '角色', width: 120 },
  { prop: 'phone', label: '手机号', width: 140 },
  { prop: 'email', label: '邮箱', width: 180 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'is_active', label: '状态', width: 80 },
]
</script>
