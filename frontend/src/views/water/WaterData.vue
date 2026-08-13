<template>
  <GenericList title="量测水数据" :apiList="getMeasurements" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getMeasurements } from '@/api'

const columns = [
  { prop: 'station_name', label: '测站', width: 160 },
  { prop: 'measure_time', label: '测量时间', width: 180 },
  { prop: 'flow_rate', label: '流量(m³/s)', width: 120 },
  { prop: 'water_level', label: '水位(m)', width: 100 },
  { prop: 'total_flow', label: '累计流量(m³)', width: 140 },
  { prop: 'source', label: '来源', width: 100 },
]
</script>
