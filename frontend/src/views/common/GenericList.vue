<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ title }}</h2>
      <div>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">新增</el-button>
      </div>
    </div>

    <div class="page-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item>
          <el-input v-model="searchForm.keyword" placeholder="搜索..." clearable style="width: 240px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column v-for="col in columns" :key="col.prop" :prop="col.prop" :label="col.label" :width="col.width" />
        <el-table-column label="创建时间" prop="created_at" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="searchForm.page"
          v-model:page-size="searchForm.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, defineProps, withDefaults } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  title: { type: String, default: '列表' },
  apiList: { type: Function, required: true },
  apiCreate: { type: Function, default: null },
  apiUpdate: { type: Function, default: null },
  apiDelete: { type: Function, default: null },
  columns: { type: Array, default: () => [] },
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const searchForm = reactive({
  keyword: '',
  page: 1,
  page_size: 20,
})

async function loadData() {
  loading.value = true
  try {
    const params = { ...searchForm }
    if (searchForm.keyword) params.search = searchForm.keyword
    const res = await props.apiList(params)
    tableData.value = res.data.results
    total.value = res.data.count
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.keyword = ''
  searchForm.page = 1
  loadData()
}

function showCreateDialog() {
  ElMessage.info('新增功能待实现')
}

function handleEdit(row) {
  ElMessage.info(`编辑: ${row.id}`)
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定要删除吗？', '提示', { type: 'warning' })
  if (props.apiDelete) {
    await props.apiDelete(row.id)
    ElMessage.success('删除成功')
    loadData()
  }
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
