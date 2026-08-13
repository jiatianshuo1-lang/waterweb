<template>
  <GenericList title="灌溉记录" :apiList="getIrrigationRecords" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getIrrigationRecords } from '@/api'

const columns = [
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'device_name', label: '设备', width: 140 },
  { prop: 'start_time', label: '开始时间', width: 180 },
  { prop: 'duration', label: '时长(分钟)', width: 100 },
  { prop: 'water_used', label: '用水量(m³)', width: 120 },
  { prop: 'energy_used', label: '用电(kWh)', width: 120 },
]
</script>
