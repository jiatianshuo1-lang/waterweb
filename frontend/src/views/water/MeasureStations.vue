<template>
  <GenericList title="量测水测站" :apiList="getMeasureStations" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getMeasureStations } from '@/api'

const columns = [
  { prop: 'code', label: '测站编码', width: 160 },
  { prop: 'name', label: '测站名称', width: 180 },
  { prop: 'station_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'last_data_time', label: '最后数据', width: 180 },
]
</script>
