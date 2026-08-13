<template>
  <GenericList title="分配方案" :apiList="getWaterAllocations" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterAllocations } from '@/api'

const columns = [
  { prop: 'code', label: '方案编号', width: 160 },
  { prop: 'name', label: '方案名称', width: 200 },
  { prop: 'allocation_type', label: '类型', width: 100 },
  { prop: 'source_name', label: '水源', width: 140 },
  { prop: 'total_amount', label: '总量(万m³)', width: 130 },
  { prop: 'period_start', label: '开始日期', width: 120 },
  { prop: 'status', label: '状态', width: 100 },
]
</script>
