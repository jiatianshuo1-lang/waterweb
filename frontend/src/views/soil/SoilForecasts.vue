<template>
  <div class="page-container">
    <div class="page-header">
      <h2>墒情预报</h2>
      <el-button type="primary" :icon="MagicStick" @click="generate">生成预报</el-button>
    </div>
    <GenericList title="" :apiList="getSoilForecasts" :columns="columns" />
  </div>
</template>

<script setup>
import GenericList from '@/views/common/GenericList.vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { getSoilForecasts, generateForecast } from '@/api'

const columns = [
  { prop: 'station_name', label: '测站', width: 160 },
  { prop: 'forecast_type', label: '预报类型', width: 120 },
  { prop: 'forecast_time', label: '预报时间', width: 180 },
  { prop: 'current_moisture', label: '当前含水率(%)', width: 160 },
  { prop: 'predicted_moisture', label: '预测含水率(%)', width: 160 },
  { prop: 'risk_level', label: '风险等级', width: 100 },
  { prop: 'advice', label: '建议措施', width: 300 },
]

async function generate() {
  try {
    const res = await generateForecast({})
    ElMessage.success(`成功生成 ${res.data.count} 条预报`)
  } catch (e) {
    console.error(e)
  }
}
</script>
