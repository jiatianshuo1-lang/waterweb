<template>
  <GenericList title="固定资产" :apiList="getAssets" :columns="columns" />
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { getAssets } from '@/api'

const columns = [
  { prop: 'code', label: '资产编号', width: 160 },
  { prop: 'name', label: '资产名称', width: 180 },
  { prop: 'asset_type', label: '类型', width: 100 },
  { prop: 'region_name', label: '区域', width: 140 },
  { prop: 'model', label: '规格型号', width: 140 },
  { prop: 'status', label: '使用状态', width: 100 },
  { prop: 'responsible_name', label: '责任人', width: 120 },
]
</script>
