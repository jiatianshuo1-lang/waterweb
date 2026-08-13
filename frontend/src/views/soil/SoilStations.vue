<template>
  <GenericList title="墒情气象测站" :apiList="getSoilStations" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getSoilStations } from '@/api'

const columns = [
  { prop: 'code', label: '测站编码', width: 160 },
  { prop: 'name', label: '测站名称', width: 180 },
  { prop: 'station_type', label: '类型', width: 120 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'soil_type', label: '土壤类型', width: 120 },
  { prop: 'status', label: '状态', width: 80 },
  { prop: 'last_data_time', label: '最后数据', width: 180 },
]
</script>
