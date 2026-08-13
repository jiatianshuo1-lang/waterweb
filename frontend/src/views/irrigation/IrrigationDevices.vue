<template>
  <GenericList title="灌溉设备" :apiList="getIrrigationDevices" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getIrrigationDevices } from '@/api'

const columns = [
  { prop: 'code', label: '设备编码', width: 160 },
  { prop: 'name', label: '设备名称', width: 180 },
  { prop: 'device_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'control_mode', label: '控制模式', width: 100 },
  { prop: 'status', label: '状态', width: 100 },
]
</script>
