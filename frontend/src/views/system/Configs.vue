<template>
  <GenericList title="系统配置" :apiList="getConfigs" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getConfigs } from '@/api'

const columns = [
  { prop: 'config_type', label: '配置类型', width: 120 },
  { prop: 'config_key', label: '配置键', width: 180 },
  { prop: 'config_value', label: '配置值', width: 300 },
  { prop: 'description', label: '说明', width: 250 },
]
</script>
