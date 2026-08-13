<template>
  <GenericList title="用水户" :apiList="getWaterUsers" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterUsers } from '@/api'

const columns = [
  { prop: 'code', label: '用户编号', width: 160 },
  { prop: 'name', label: '用户名称', width: 180 },
  { prop: 'user_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'policy_name', label: '适用政策', width: 140 },
  { prop: 'water_meter', label: '水表编号', width: 140 },
]
</script>
