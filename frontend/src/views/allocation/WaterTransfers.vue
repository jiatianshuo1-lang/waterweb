<template>
  <GenericList title="调水调度" :apiList="getWaterTransfers" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterTransfers } from '@/api'

const columns = [
  { prop: 'code', label: '调水编号', width: 160 },
  { prop: 'transfer_type', label: '类型', width: 120 },
  { prop: 'from_region_name', label: '调出区域', width: 140 },
  { prop: 'to_region_name', label: '调入区域', width: 140 },
  { prop: 'amount', label: '调水量(万m³)', width: 140 },
  { prop: 'planned_start', label: '计划开始', width: 180 },
  { prop: 'status', label: '状态', width: 100 },
]
</script>
