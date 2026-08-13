<template>
  <GenericList title="墒情数据" :apiList="getSoilData" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getSoilData } from '@/api'

const columns = [
  { prop: 'station_name', label: '测站', width: 160 },
  { prop: 'measure_time', label: '测量时间', width: 180 },
  { prop: 'soil_moisture_avg', label: '平均含水率(%)', width: 150 },
  { prop: 'soil_temperature_10', label: '10cm地温(℃)', width: 150 },
  { prop: 'soil_ph', label: 'pH值', width: 100 },
  { prop: 'soil_salinity', label: '盐度(dS/m)', width: 130 },
]
</script>
