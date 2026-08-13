<template>
  <div class="page-container">
    <div class="page-header">
      <h2>巡检管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建巡检</el-button>
    </div>

    <div class="page-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="编号/标题">
          <el-input v-model="searchForm.keyword" placeholder="输入关键词" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.template_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="日常巡检" value="daily" />
            <el-option label="周巡检" value="weekly" />
            <el-option label="月巡检" value="monthly" />
            <el-option label="专项巡检" value="special" />
            <el-option label="应急巡检" value="emergency" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="code" label="巡检编号" width="180" />
        <el-table-column prop="title" label="巡检标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="template_type" label="类型" width="100">
          <template #default="{ row }">{{ typeText(row.template_type) }}</template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ priorityText(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region_name" label="巡检区域" width="140" />
        <el-table-column prop="inspector_names" label="巡检人员" width="160">
          <template #default="{ row }">{{ row.inspector_names?.join(', ') || '-' }}</template>
        </el-table-column>
        <el-table-column prop="planned_start" label="计划开始" width="160">
          <template #default="{ row }">{{ formatTime(row.planned_start) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="dark">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">查看</el-button>
            <el-button v-if="row.status === 'pending'" link type="success" size="small" @click="startInspection(row)">开始</el-button>
            <el-button v-if="row.status === 'in_progress'" link type="warning" size="small" @click="completeInspection(row)">完成</el-button>
            <el-button v-if="['pending', 'in_progress'].includes(row.status)" link type="danger" size="small" @click="cancelInspection(row)">取消</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="巡检标题">
          <el-input v-model="createForm.title" placeholder="请输入巡检标题" />
        </el-form-item>
        <el-form-item label="巡检类型">
          <el-select v-model="createForm.template_type" style="width: 100%">
            <el-option label="日常巡检" value="daily" />
            <el-option label="周巡检" value="weekly" />
            <el-option label="月巡检" value="monthly" />
            <el-option label="专项巡检" value="special" />
            <el-option label="应急巡检" value="emergency" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="createForm.priority" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="巡检人员">
          <el-input v-model="createForm.inspector_ids" placeholder="临时输入人员ID，实际应使用用户选择" />
        </el-form-item>
        <el-form-item label="计划开始">
          <el-date-picker v-model="createForm.planned_start" type="datetime" placeholder="选择时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="计划结束">
          <el-date-picker v-model="createForm.planned_end" type="datetime" placeholder="选择时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="巡检说明">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getInspections, createInspection, startInspection as startApi, completeInspection as completeApi, cancelInspection as cancelApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)

const searchForm = reactive({
  keyword: '',
  template_type: '',
  status: '',
  page: 1,
  page_size: 20,
})

const createForm = reactive({
  title: '',
  template_type: 'daily',
  priority: 'medium',
  inspector_ids: [],
  planned_start: '',
  planned_end: '',
  description: '',
})

const dialogTitle = ref('新建巡检')

async function loadData() {
  loading.value = true
  try {
    const params = { ...searchForm }
    if (searchForm.keyword) {
      params.search = searchForm.keyword
    }
    const res = await getInspections(params)
    tableData.value = res.data.results
    total.value = res.data.count
  } catch (e) {
    console.error('Failed to load inspections:', e)
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.keyword = ''
  searchForm.template_type = ''
  searchForm.status = ''
  searchForm.page = 1
  loadData()
}

function showCreateDialog() {
  Object.assign(createForm, {
    title: '',
    template_type: 'daily',
    priority: 'medium',
    inspector_ids: [],
    planned_start: '',
    planned_end: '',
    description: '',
  })
  dialogVisible.value = true
}

async function handleCreate() {
  try {
    await createInspection(createForm)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    console.error('Failed to create inspection:', e)
  }
}

async function startInspection(row) {
  await ElMessageBox.confirm('确定开始该巡检任务？', '提示', { type: 'info' })
  await startApi(row.id)
  ElMessage.success('已开始巡检')
  loadData()
}

async function completeInspection(row) {
  await ElMessageBox.confirm('确定完成该巡检？是否创建工单处理异常项？', '完成巡检', {
    type: 'warning',
    confirmButtonText: '完成并创建工单',
    cancelButtonText: '仅完成',
    distinguishCancelAndClose: true,
  }).then(async () => {
    await completeApi(row.id, { create_work_order: true })
  }).catch(async (action) => {
    if (action === 'cancel') {
      await completeApi(row.id, { create_work_order: false })
    }
  })
  ElMessage.success('巡检已完成')
  loadData()
}

async function cancelInspection(row) {
  await ElMessageBox.confirm('确定取消该巡检任务？', '提示', { type: 'warning' })
  await cancelApi(row.id, {})
  ElMessage.success('已取消')
  loadData()
}

function viewDetail(row) {
  ElMessage.info(`查看巡检详情: ${row.code}`)
}

function typeText(type) {
  const map = { daily: '日常', weekly: '周巡检', monthly: '月巡检', special: '专项', emergency: '应急' }
  return map[type] || type
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
  const map = { pending: '待处理', in_progress: '进行中', completed: '已完成', cancelled: '已取消', overdue: '已逾期' }
  return map[s] || s
}

function statusType(s) {
  const map = { pending: 'warning', in_progress: 'primary', completed: 'success', cancelled: 'info', overdue: 'danger' }
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
