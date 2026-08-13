<template>
  <GenericList title="操作日志" :apiList="getOperationLogs" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getOperationLogs } from '@/api'

const columns = [
  { prop: 'user_name', label: '操作人', width: 120 },
  { prop: 'log_type', label: '操作类型', width: 100 },
  { prop: 'module', label: '模块', width: 120 },
  { prop: 'action', label: '操作', width: 200 },
  { prop: 'ip_address', label: 'IP地址', width: 140 },
  { prop: 'status', label: '状态', width: 80 },
]
</script>
