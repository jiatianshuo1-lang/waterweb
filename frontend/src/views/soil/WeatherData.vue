<template>
  <GenericList title="气象数据" :apiList="getWeatherData" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWeatherData } from '@/api'

const columns = [
  { prop: 'station_name', label: '测站', width: 160 },
  { prop: 'measure_time', label: '测量时间', width: 180 },
  { prop: 'temperature', label: '气温(℃)', width: 100 },
  { prop: 'humidity', label: '湿度(%)', width: 100 },
  { prop: 'rainfall', label: '降水(mm)', width: 100 },
  { prop: 'wind_speed', label: '风速(m/s)', width: 110 },
  { prop: 'solar_radiation', label: '太阳辐射(W/m²)', width: 150 },
]
</script>
