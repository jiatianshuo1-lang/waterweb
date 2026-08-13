<template>
  <div class="ai-assistant-float">
    <div v-if="!isOpen" class="ai-trigger" @click="openChat">
      <el-icon :size="24"><ChatDotRound /></el-icon>
      <span class="ai-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
    </div>

    <transition name="slide-up">
      <div v-if="isOpen" class="ai-chat-panel">
        <div class="chat-header">
          <div class="header-info">
            <el-icon :size="20"><ChatDotRound /></el-icon>
            <span>AI智能助手</span>
            <el-tag size="small" type="success" effect="plain">在线</el-tag>
          </div>
          <div class="header-actions">
            <el-icon @click="newChat" title="新对话" class="action-icon"><Plus /></el-icon>
            <el-icon @click="toggleHistory" title="历史记录" class="action-icon"><Clock /></el-icon>
            <el-icon @click="closeChat" title="关闭" class="action-icon"><Close /></el-icon>
          </div>
        </div>

        <div v-if="showHistory" class="history-panel">
          <div class="history-header">
            <span>历史会话</span>
            <el-icon @click="toggleHistory"><Close /></el-icon>
          </div>
          <div class="history-list">
            <div
              v-for="session in sessions"
              :key="session.session_id"
              class="history-item"
              :class="{ active: currentSessionId === session.session_id }"
              @click="loadSession(session)"
            >
              <div class="session-title">{{ session.title || '新对话' }}</div>
              <div class="session-meta">
                <span class="message-count">{{ session.message_count }} 条消息</span>
                <span class="session-time">{{ formatTime(session.last_message_time) }}</span>
              </div>
            </div>
            <div v-if="sessions.length === 0" class="empty-history">
              <el-empty description="暂无历史会话" :image-size="60" />
            </div>
          </div>
        </div>

        <div v-else class="chat-body" ref="chatBodyRef">
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-icon">
              <el-icon :size="48" color="#409eff"><ChatDotRound /></el-icon>
            </div>
            <h3>灌区管理AI助手</h3>
            <p>我可以帮您解答灌区管理相关问题，包括：</p>
            <div class="suggestions">
              <div class="suggestion" @click="sendQuickMessage('当前灌区的水位情况如何？')">
                <el-icon><Pouring /></el-icon>
                <span>查询水位情况</span>
              </div>
              <div class="suggestion" @click="sendQuickMessage('墒情监测数据有异常吗？')">
                <el-icon><DataAnalysis /></el-icon>
                <span>墒情异常查询</span>
              </div>
              <div class="suggestion" @click="sendQuickMessage('如何进行科学灌溉？')">
                <el-icon><Reading /></el-icon>
                <span>灌溉建议</span>
              </div>
              <div class="suggestion" @click="sendQuickMessage('帮我生成巡检计划')">
                <el-icon><EditPen /></el-icon>
                <span>生成巡检计划</span>
              </div>
            </div>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-item"
            :class="msg.role"
          >
            <div class="avatar" :class="msg.role">
              <el-icon v-if="msg.role === 'user'" :size="18"><User /></el-icon>
              <el-icon v-else :size="18"><Monitor /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
              <div v-if="msg.role === 'assistant' && msg.response_time" class="message-meta">
                响应时间 {{ msg.response_time }}s
              </div>
            </div>
          </div>

          <div v-if="isLoading" class="message-item assistant">
            <div class="avatar assistant">
              <el-icon :size="18"><Monitor /></el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="1"
              resize="none"
              placeholder="输入您的问题..."
              @keydown.enter.exact.prevent="handleSend"
              :disabled="isLoading"
            />
            <el-button
              type="primary"
              :icon="Promotion"
              circle
              @click="handleSend"
              :loading="isLoading"
              :disabled="!inputMessage.trim()"
            />
          </div>
          <div class="input-hint">按 Enter 发送，Shift+Enter 换行</div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>import { ref, nextTick, onMounted } from 'vue';
import { ChatDotRound, Plus, Clock, Close, User, Monitor, Pouring, DataAnalysis, Reading, EditPen, Promotion } from '@element-plus/icons-vue';
import MarkdownIt from 'markdown-it';
import { sendAiMessage, getAiSessions, createAiSession, deleteAiSession } from '@/api';
const md = new MarkdownIt({ html: false, linkify: true, breaks: true });
const isOpen = ref(false);
const showHistory = ref(false);
const inputMessage = ref('');
const messages = ref([]);
const isLoading = ref(false);
const unreadCount = ref(0);
const currentSessionId = ref('');
const sessions = ref([]);
const chatBodyRef = ref(null);
function openChat() {
 isOpen.value = true;
 unreadCount.value = 0;
 if (!currentSessionId.value) {
 loadSessions();
 }
 scrollToBottom();
}
function closeChat() {
 isOpen.value = false;
 showHistory.value = false;
}
function toggleHistory() {
 showHistory.value = !showHistory.value;
 if (showHistory.value) {
 loadSessions();
 }
}
async function loadSessions() {
 try {
 const res = await getAiSessions();
 sessions.value = res.data || [];
 }
 catch (e) {
 console.error('Failed to load sessions:', e);
 }
}
async function newChat() {
 messages.value = [];
 showHistory.value = false;
 try {
 const res = await createAiSession();
 currentSessionId.value = res.data.session_id;
 }
 catch (e) {
 console.error('Failed to create session:', e);
 }
}
async function loadSession(session) {
 currentSessionId.value = session.session_id;
 messages.value = [];
 showHistory.value = false;
 try {
 const res = await getAiSessions();
 const found = (res.data || []).find(s => s.session_id === session.session_id);
 if (found) {
 const messagesRes = await fetch(`/api/v1/ai/chat/history/?session_id=${session.session_id}`).then(r => r.json());
 messages.value = messagesRes.data || [];
 scrollToBottom();
 }
 }
 catch (e) {
 console.error('Failed to load session:', e);
 }
}
async function handleSend() {
 const text = inputMessage.value.trim();
 if (!text || isLoading.value)
 return;
 const userMsg = { role: 'user', content: text };
 messages.value.push(userMsg);
 inputMessage.value = '';
 isLoading.value = true;
 scrollToBottom();
 try {
 const payload = { message: text };
 if (currentSessionId.value) {
 payload.session_id = currentSessionId.value;
 }
 const res = await sendAiMessage(payload);
 currentSessionId.value = res.data.session_id;
 messages.value.push({
 role: 'assistant',
 content: res.data.response,
 response_time: res.data.response_time,
 });
 scrollToBottom();
 }
 catch (err) {
 messages.value.push({
 role: 'assistant',
 content: '抱歉，服务暂时不可用，请稍后重试。',
 response_time: 0,
 });
 }
 finally {
 isLoading.value = false;
 }
}
function sendQuickMessage(text) {
 inputMessage.value = text;
 handleSend();
}
function formatMessage(text) {
 return md.render(text);
}
function formatTime(time) {
 if (!time)
 return '';
 const d = new Date(time);
 const now = new Date();
 const diff = (now - d) / 1000;
 if (diff < 60)
 return '刚刚';
 if (diff < 3600)
 return `${Math.floor(diff / 60)} 分钟前`;
 if (diff < 86400)
 return `${Math.floor(diff / 3600)} 小时前`;
 return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
}
function scrollToBottom() {
 nextTick(() => {
 if (chatBodyRef.value) {
 chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight;
 }
 });
}
onMounted(() => {
 // 自动打开可以通过URL参数
});
</script>

<style lang="scss" scoped>
.ai-assistant-float {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 9999;
}

.ai-trigger {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: transform 0.3s, box-shadow 0.3s;
  position: relative;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.6);
  }

  .ai-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    background: #f56c6c;
    color: #fff;
    font-size: 12px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.ai-chat-panel {
  width: 400px;
  height: 560px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;

  .header-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 12px;

    .action-icon {
      cursor: pointer;
      transition: transform 0.2s;

      &:hover {
        transform: scale(1.2);
      }
    }
  }
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #dcdfe6;
    border-radius: 3px;
  }
}

.welcome-section {
  text-align: center;
  padding: 20px 10px;

  .welcome-icon {
    margin-bottom: 12px;
  }

  h3 {
    color: #303133;
    margin-bottom: 8px;
  }

  p {
    color: #909399;
    font-size: 14px;
    margin-bottom: 16px;
  }
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.suggestion {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #606266;

  &:hover {
    border-color: #409eff;
    color: #409eff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  }
}

.message-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
      color: #fff;
      border-radius: 12px 2px 12px 12px;
      max-width: 80%;
    }
  }

  &.assistant {
    .message-content {
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 2px 12px 12px 12px;
      max-width: 85%;
    }
  }

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.user {
      background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
      color: #fff;
    }

    &.assistant {
      background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
      color: #fff;
    }
  }

  .message-content {
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;

    :deep(p) {
      margin: 0 0 8px;
      &:last-child {
        margin-bottom: 0;
      }
    }

    :deep(pre) {
      background: #1e1e1e;
      color: #d4d4d4;
      padding: 10px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 13px;
    }

    :deep(code) {
      background: rgba(0, 0, 0, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: Consolas, Monaco, monospace;
      font-size: 13px;
    }

    :deep(pre code) {
      background: transparent;
      padding: 0;
    }

    :deep(ul), :deep(ol) {
      padding-left: 20px;
      margin: 4px 0;
    }

    :deep(a) {
      color: inherit;
      text-decoration: underline;
    }
  }

  .message-meta {
    font-size: 11px;
    color: #909399;
    margin-top: 4px;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 6px 0;

  span {
    width: 8px;
    height: 8px;
    background: #c0c4cc;
    border-radius: 50%;
    animation: typing 1.4s infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  background: #fff;

  .input-wrapper {
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }

  :deep(.el-textarea) {
    flex: 1;
  }

  :deep(.el-textarea__inner) {
    border-radius: 10px;
    padding: 10px 14px;
  }

  .input-hint {
    font-size: 11px;
    color: #c0c4cc;
    margin-top: 4px;
    text-align: right;
  }
}

.history-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;

  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
    font-weight: 600;
    color: #303133;
  }

  .history-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .history-item {
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-bottom: 4px;

    &:hover {
      background: #f5f7fa;
    }

    &.active {
      background: #ecf5ff;
      border: 1px solid #d9ecff;
    }

    .session-title {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .session-meta {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #909399;

      .session-time {
        flex-shrink: 0;
      }
    }
  }

  .empty-history {
    padding: 40px 0;
  }
}
</style>
