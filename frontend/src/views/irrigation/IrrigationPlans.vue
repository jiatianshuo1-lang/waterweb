<template>
  <GenericList title="灌溉计划" :apiList="getIrrigationPlans" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getIrrigationPlans } from '@/api'

const columns = [
  { prop: 'code', label: '计划编号', width: 160 },
  { prop: 'name', label: '计划名称', width: 200 },
  { prop: 'plan_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'start_time', label: '开始时间', width: 180 },
  { prop: 'status', label: '状态', width: 100 },
]
</script>
