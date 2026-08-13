<template>
  <GenericList title="会议管理" :apiList="getMeetings" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getMeetings } from '@/api'

const columns = [
  { prop: 'title', label: '会议主题', width: 200 },
  { prop: 'meeting_type', label: '类型', width: 100 },
  { prop: 'start_time', label: '开始时间', width: 180 },
  { prop: 'end_time', label: '结束时间', width: 180 },
  { prop: 'location', label: '地点', width: 180 },
  { prop: 'host_name', label: '主持人', width: 120 },
  { prop: 'status', label: '状态', width: 100 },
]
</script>
