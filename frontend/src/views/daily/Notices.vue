<template>
  <GenericList title="通知公告" :apiList="getNotices" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getNotices } from '@/api'

const columns = [
  { prop: 'title', label: '标题', width: 300 },
  { prop: 'notice_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 120 },
  { prop: 'is_top', label: '置顶', width: 80 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'published_at', label: '发布时间', width: 180 },
]
</script>
