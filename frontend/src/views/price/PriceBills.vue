<template>
  <GenericList title="水费账单" :apiList="getWaterBills" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterBills } from '@/api'

const columns = [
  { prop: 'code', label: '账单编号', width: 160 },
  { prop: 'user_name', label: '用水户', width: 160 },
  { prop: 'billing_period_start', label: '计费期开始', width: 120 },
  { prop: 'billing_period_end', label: '计费期结束', width: 120 },
  { prop: 'usage', label: '用水量(m³)', width: 120 },
  { prop: 'total_fee', label: '应缴(元)', width: 100 },
  { prop: 'paid_fee', label: '已缴(元)', width: 100 },
  { prop: 'status', label: '状态', width: 80 },
]
</script>
