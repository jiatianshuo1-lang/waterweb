<template>
  <GenericList title="文档资料" :apiList="getDocuments" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getDocuments } from '@/api'

const columns = [
  { prop: 'title', label: '文档标题', width: 250 },
  { prop: 'doc_type', label: '类型', width: 100 },
  { prop: 'file_name', label: '文件名', width: 200 },
  { prop: 'file_size', label: '大小', width: 100 },
  { prop: 'region_name', label: '区域', width: 120 },
  { prop: 'downloads', label: '下载次数', width: 100 },
]
</script>
