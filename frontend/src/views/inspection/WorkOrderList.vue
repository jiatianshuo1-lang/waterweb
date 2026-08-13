<template>
  <div class="page-container">
    <div class="page-header">
      <h2>工单管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建工单</el-button>
    </div>

    <div class="page-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="编号/标题">
          <el-input v-model="searchForm.keyword" placeholder="输入关键词" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="待受理" value="pending" />
            <el-option label="已派单" value="assigned" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已验收" value="verified" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.order_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="巡检发现" value="inspection_issue" />
            <el-option label="用户上报" value="user_report" />
            <el-option label="设备故障" value="device_fault" />
            <el-option label="日常维护" value="routine_maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="code" label="工单编号" width="180" />
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="order_type" label="类型" width="110">
          <template #default="{ row }">{{ typeText(row.order_type) }}</template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ priorityText(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region_name" label="区域" width="120" />
        <el-table-column prop="assignee_name" label="处理人" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="dark">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'pending'" link type="success" size="small" @click="assignOrder(row)">派单</el-button>
            <el-button v-if="row.status === 'assigned'" link type="warning" size="small" @click="startOrder(row)">开始</el-button>
            <el-button v-if="row.status === 'in_progress'" link type="primary" size="small" @click="completeOrder(row)">完成</el-button>
            <el-button v-if="row.status === 'completed'" link type="success" size="small" @click="verifyOrder(row)">验收</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="searchForm.page"
          v-model:page-size="searchForm.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getWorkOrders, createWorkOrder, assignWorkOrder, startWorkOrder, completeWorkOrder, verifyWorkOrder } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const searchForm = reactive({
  keyword: '',
  status: '',
  order_type: '',
  page: 1,
  page_size: 20,
})

async function loadData() {
  loading.value = true
  try {
    const res = await getWorkOrders(searchForm)
    tableData.value = res.data.results
    total.value = res.data.count
  } catch (e) {
    console.error('Failed to load work orders:', e)
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.order_type = ''
  searchForm.page = 1
  loadData()
}

function showCreateDialog() {
  ElMessage.info('新建工单对话框')
}

async function assignOrder(row) {
  const { value } = await ElMessageBox.prompt('请输入处理人ID', '派单', { confirmButtonText: '确定' })
  await assignWorkOrder(row.id, { assignee: parseInt(value) })
  ElMessage.success('派单成功')
  loadData()
}

async function startOrder(row) {
  await startWorkOrder(row.id, {})
  ElMessage.success('已开始处理')
  loadData()
}

async function completeOrder(row) {
  const { value } = await ElMessageBox.prompt('请输入解决方案', '完成工单', { type: 'textarea', confirmButtonText: '确定' })
  await completeWorkOrder(row.id, { solution: value })
  ElMessage.success('工单已完成')
  loadData()
}

async function verifyOrder(row) {
  try {
    await ElMessageBox.confirm('是否验收通过？', '验收', { type: 'warning' })
    await verifyWorkOrder(row.id, { satisfied: true, satisfaction: 5 })
    ElMessage.success('验收通过')
    loadData()
  } catch {}
}

function viewDetail(row) {
  ElMessage.info(`查看工单详情: ${row.code}`)
}

function typeText(t) {
  const map = { inspection_issue: '巡检发现', user_report: '用户上报', device_fault: '设备故障', routine_maintenance: '日常维护', emergency: '应急处置' }
  return map[t] || t
}

function priorityText(p) {
  const map = { low: '低', medium: '中', high: '高', urgent: '紧急' }
  return map[p] || p
}

function priorityType(p) {
  const map = { low: 'info', medium: 'warning', high: 'danger', urgent: 'danger' }
  return map[p] || 'info'
}

function statusText(s) {
  const map = { pending: '待受理', assigned: '已派单', in_progress: '处理中', completed: '已完成', verified: '已验收', closed: '已关闭', rejected: '已驳回' }
  return map[s] || s
}

function statusType(s) {
  const map = { pending: 'warning', assigned: 'primary', in_progress: 'primary', completed: 'success', verified: 'success', closed: 'info', rejected: 'danger' }
  return map[s] || 'info'
}

function formatTime(t) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
