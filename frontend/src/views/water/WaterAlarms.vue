<template>
  <GenericList title="水量告警" :apiList="getWaterAlarms" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getWaterAlarms } from '@/api'

const columns = [
  { prop: 'station_name', label: '测站', width: 160 },
  { prop: 'alarm_type', label: '告警类型', width: 120 },
  { prop: 'level', label: '级别', width: 80 },
  { prop: 'title', label: '告警标题', width: 200 },
  { prop: 'triggered_at', label: '触发时间', width: 180 },
  { prop: 'is_resolved', label: '是否处理', width: 100 },
]
</script>
