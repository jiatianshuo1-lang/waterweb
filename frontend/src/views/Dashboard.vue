<template>
  <div class="dashboard">
    <div class="welcome-banner">
      <div class="banner-content">
        <h2>{{ greeting }}，{{ userStore.userInfo?.real_name }}！</h2>
        <p>今日是 {{ today }}，祝您工作顺利</p>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.inspection_pending || 0 }}</div>
          <div class="stat-label">待处理巡检</div>
          <el-icon class="stat-icon"><Tickets /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-success">
          <div class="stat-value">{{ stats.workorder_pending || 0 }}</div>
          <div class="stat-label">待处理工单</div>
          <el-icon class="stat-icon"><Document /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-warning">
          <div class="stat-value">{{ stats.water_alerts || 0 }}</div>
          <div class="stat-label">水量告警</div>
          <el-icon class="stat-icon"><Bell /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-danger">
          <div class="stat-value">{{ stats.soil_alerts || 0 }}</div>
          <div class="stat-label">墒情异常</div>
          <el-icon class="stat-icon"><Warning /></el-icon>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="16">
        <div class="page-card chart-card">
          <div class="card-header">
            <h3>水量监测趋势</h3>
            <el-radio-group v-model="waterRange" size="small">
              <el-radio-button :value="7">近7天</el-radio-button>
              <el-radio-button :value="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="waterChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="8">
        <div class="page-card chart-card">
          <div class="card-header">
            <h3>灌溉设备状态</h3>
          </div>
          <div ref="deviceChartRef" class="chart-container small"></div>
        </div>
        <div class="page-card chart-card" style="margin-top: 16px">
          <div class="card-header">
            <h3>快捷入口</h3>
          </div>
          <div class="quick-actions">
            <div class="quick-item" @click="$router.push('/inspection/list')">
              <el-icon :size="24" color="#409eff"><Tickets /></el-icon>
              <span>发起巡检</span>
            </div>
            <div class="quick-item" @click="$router.push('/inspection/workorders')">
              <el-icon :size="24" color="#67c23a"><Document /></el-icon>
              <span>处理工单</span>
            </div>
            <div class="quick-item" @click="$router.push('/irrigation/plans')">
              <el-icon :size="24" color="#e6a23c"><Aim /></el-icon>
              <span>灌溉计划</span>
            </div>
            <div class="quick-item" @click="$router.push('/soil/forecasts')">
              <el-icon :size="24" color="#f56c6c"><Monitor /></el-icon>
              <span>墒情预报</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :xs="24" :lg="12">
        <div class="page-card">
          <div class="card-header">
            <h3>最新公告</h3>
            <el-link type="primary" :underline="false" @click="$router.push('/daily/notices')">查看更多</el-link>
          </div>
          <div class="notice-list">
            <div v-for="notice in notices" :key="notice.id" class="notice-item">
              <el-tag v-if="notice.is_top" type="danger" size="small">置顶</el-tag>
              <span class="notice-title">{{ notice.title }}</span>
              <span class="notice-date">{{ formatDate(notice.published_at) }}</span>
            </div>
            <el-empty v-if="notices.length === 0" description="暂无公告" :image-size="60" />
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="page-card">
          <div class="card-header">
            <h3>今日会议</h3>
            <el-link type="primary" :underline="false" @click="$router.push('/daily/meetings')">查看更多</el-link>
          </div>
          <div class="meeting-list">
            <div v-for="meeting in meetings" :key="meeting.id" class="meeting-item">
              <div class="meeting-time">{{ formatTime(meeting.start_time) }}</div>
              <div class="meeting-info">
                <div class="meeting-title">{{ meeting.title }}</div>
                <div class="meeting-meta">
                  <el-icon><Location /></el-icon> {{ meeting.location }}
                  <el-icon><User /></el-icon> {{ meeting.host_name }}
                </div>
              </div>
              <el-tag :type="meeting.status === 'planned' ? 'info' : meeting.status === 'ongoing' ? 'success' : ''">
                {{ statusText(meeting.status) }}
              </el-tag>
            </div>
            <el-empty v-if="meetings.length === 0" description="今日暂无会议" :image-size="60" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import * as echarts from 'echarts';
import { Tickets, Document, Bell, Warning, Location, User } from '@element-plus/icons-vue';
import { useUserStore } from '@/stores/user';
import { getInspectionStats, getWorkOrderStats, getWaterStats, getSoilOverview, getNotices, getMeetings } from '@/api';
const userStore = useUserStore();
const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
const greeting = computed(() => {
 const hour = new Date().getHours();
 if (hour < 6)
 return '凌晨好';
 if (hour < 12)
 return '上午好';
 if (hour < 14)
 return '中午好';
 if (hour < 18)
 return '下午好';
 return '晚上好';
});
const stats = ref({});
const notices = ref([]);
const meetings = ref([]);
const waterRange = ref(7);
const waterChartRef = ref(null);
const deviceChartRef = ref(null);
let waterChart = null;
let deviceChart = null;
async function loadData() {
 try {
 const [inspStats, woStats, waterStats, soilOverview, noticesRes, meetingsRes] = await Promise.all([
 getInspectionStats(),
 getWorkOrderStats(),
 getWaterStats(),
 getSoilOverview().catch(() => ({ data: { alerts: 0 } })),
 getNotices({ page_size: 5 }).catch(() => ({ data: { results: [] } })),
 getMeetings({ page_size: 5 }).catch(() => ({ data: { results: [] } })),
 ]);
 stats.value = {
 inspection_pending: inspStats.data?.pending || 0,
 workorder_pending: woStats.data?.pending || 0,
 water_alerts: waterStats.data?.alerts_unresolved || 0,
 soil_alerts: soilOverview.data?.alerts || 0,
 };
 notices.value = noticesRes.data?.results || [];
 meetings.value = meetingsRes.data?.results || [];
 initCharts();
 }
 catch (e) {
 console.error('Failed to load dashboard data:', e);
 }
}
function initCharts() {
 if (waterChartRef.value) {
 waterChart = echarts.init(waterChartRef.value);
 waterChart.setOption({
 tooltip: { trigger: 'axis' },
 legend: { data: ['流量(m³/s)', '水位(m)'] },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'category', boundaryGap: false, data: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'] },
 yAxis: [
 { type: 'value', name: '流量(m³/s)' },
 { type: 'value', name: '水位(m)' },
 ],
 series: [
 {
 name: '流量(m³/s)',
 type: 'line',
 smooth: true,
 data: [120, 132, 101, 134, 90, 230, 210],
 itemStyle: { color: '#409eff' },
 areaStyle: { color: 'rgba(64, 158, 255, 0.1)' },
 },
 {
 name: '水位(m)',
 type: 'line',
 yAxisIndex: 1,
 smooth: true,
 data: [5.2, 5.3, 5.1, 5.4, 5.0, 5.6, 5.5],
 itemStyle: { color: '#67c23a' },
 },
 ],
 });
 }
 if (deviceChartRef.value) {
 deviceChart = echarts.init(deviceChartRef.value);
 deviceChart.setOption({
 tooltip: { trigger: 'item' },
 legend: { bottom: '0%' },
 series: [
 {
 type: 'pie',
 radius: ['45%', '70%'],
 avoidLabelOverlap: false,
 label: { show: false },
 emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
 data: [
 { value: 80, name: '在线', itemStyle: { color: '#67c23a' } },
 { value: 12, name: '离线', itemStyle: { color: '#909399' } },
 { value: 5, name: '运行中', itemStyle: { color: '#409eff' } },
 { value: 3, name: '故障', itemStyle: { color: '#f56c6c' } },
 ],
 },
 ],
 });
 }
}
function formatDate(dateStr) {
 if (!dateStr)
 return '';
 return new Date(dateStr).toLocaleDateString('zh-CN');
}
function formatTime(dateStr) {
 if (!dateStr)
 return '';
 return new Date(dateStr).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}
function statusText(status) {
 const map = { planned: '待开始', ongoing: '进行中', completed: '已完成' };
 return map[status] || status;
}
function handleResize() {
 waterChart?.resize();
 deviceChart?.resize();
}
onMounted(() => {
 loadData();
 window.addEventListener('resize', handleResize);
});
onUnmounted(() => {
 window.removeEventListener('resize', handleResize);
 waterChart?.dispose();
 deviceChart?.dispose();
});
watch(waterRange, () => {
 // reload chart data based on range
});
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 20px;
}

.welcome-banner {
  background: linear-gradient(135deg, #409eff 0%, #2a5298 100%);
  border-radius: 12px;
  padding: 28px 32px;
  color: #fff;
  margin-bottom: 20px;

  h2 {
    font-size: 22px;
    margin-bottom: 6px;
  }

  p {
    font-size: 14px;
    opacity: 0.9;
  }
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;

  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 14px;
    color: #909399;
  }

  .stat-icon {
    position: absolute;
    right: 16px;
    top: 16px;
    font-size: 36px;
    opacity: 0.15;
  }
}

.chart-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.chart-container {
  height: 320px;

  &.small {
    height: 220px;
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #606266;

  &:hover {
    background: #f5f7fa;
    transform: translateY(-2px);
  }
}

.notice-list {
  .notice-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f2f5;

    &:last-child {
      border-bottom: none;
    }

    .notice-title {
      flex: 1;
      color: #303133;
      font-size: 14px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .notice-date {
      font-size: 12px;
      color: #c0c4cc;
    }
  }
}

.meeting-list {
  .meeting-item {
    display: flex;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid #f0f2f5;
    align-items: flex-start;

    &:last-child {
      border-bottom: none;
    }

    .meeting-time {
      font-size: 14px;
      font-weight: 600;
      color: #409eff;
      min-width: 60px;
    }

    .meeting-info {
      flex: 1;

      .meeting-title {
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
      }

      .meeting-meta {
        font-size: 12px;
        color: #909399;
        display: flex;
        gap: 12px;

        .el-icon {
          vertical-align: middle;
          margin-right: 2px;
        }
      }
    }
  }
}
</style>
