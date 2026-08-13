<template>
  <GenericList title="水源管理" :apiList="getWaterSources" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterSources } from '@/api'

const columns = [
  { prop: 'code', label: '水源编码', width: 160 },
  { prop: 'name', label: '水源名称', width: 180 },
  { prop: 'source_type', label: '类型', width: 100 },
  { prop: 'region', label: '区域', width: 140 },
  { prop: 'capacity', label: '容量(万m³)', width: 120 },
  { prop: 'current_storage', label: '当前蓄水(万m³)', width: 140 },
]
</script>
