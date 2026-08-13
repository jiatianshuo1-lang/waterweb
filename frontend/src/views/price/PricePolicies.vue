<template>
  <GenericList title="水价政策" :apiList="getWaterPolicies" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterPolicies } from '@/api'

const columns = [
  { prop: 'code', label: '政策编号', width: 160 },
  { prop: 'name', label: '政策名称', width: 200 },
  { prop: 'policy_type', label: '类型', width: 120 },
  { prop: 'pricing_mode', label: '计价模式', width: 120 },
  { prop: 'base_price', label: '基础水价(元/m³)', width: 150 },
  { prop: 'start_date', label: '生效日期', width: 120 },
  { prop: 'is_active', label: '启用', width: 80 },
]
</script>
