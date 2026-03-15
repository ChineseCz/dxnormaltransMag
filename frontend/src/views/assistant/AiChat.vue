<template>
  <div class="ai-chat-page flex h-full" style="background:#060d1a;">
    <!-- ═══════ 左栏：会话列表 ═══════ -->
    <div class="w-[260px] flex-shrink-0 flex flex-col border-r" style="border-color:rgba(51,65,85,0.4); background:rgba(8,14,29,0.95);">
      <!-- 新建按钮 -->
      <div class="p-3">
        <el-button class="w-full" @click="newConversation"
                   style="background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(168,85,247,0.15)); border:1px solid rgba(236,72,153,0.3); color:#f472b6; font-weight:600;">
          <el-icon class="mr-1"><Plus /></el-icon>新建对话
        </el-button>
      </div>

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto px-2 pb-2 space-y-1">
        <div v-for="conv in conversations" :key="conv.id"
             class="conv-item group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
             :class="conv.id === activeConvId ? 'conv-active' : ''"
             @click="switchConversation(conv.id)">
          <el-icon size="14" :style="`color:${conv.id === activeConvId ? '#f472b6' : '#475569'}`"><ChatDotRound /></el-icon>
          <span class="flex-1 text-xs truncate" :class="conv.id === activeConvId ? 'text-slate-200' : 'text-slate-400'">
            {{ conv.title }}
          </span>
          <el-icon size="12" class="text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-400"
                   @click.stop="deleteConversation(conv.id)"><Close /></el-icon>
        </div>
        <div v-if="conversations.length === 0" class="text-center py-10">
          <el-icon size="32" style="color:#1e293b;"><ChatDotRound /></el-icon>
          <p class="text-slate-700 text-xs mt-2">暂无对话记录</p>
        </div>
      </div>
    </div>

    <!-- ═══════ 右栏：主对话区 ═══════ -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 顶栏：上下文面板 -->
      <div class="flex-shrink-0 px-5 py-3 border-b flex items-center justify-between"
           style="border-color:rgba(51,65,85,0.3); background:rgba(10,18,36,0.7);">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center"
               style="background:linear-gradient(135deg,#ec4899,#8b5cf6); box-shadow:0 0 12px rgba(236,72,153,0.3);">
            <el-icon size="16" style="color:#fff;"><MagicStick /></el-icon>
          </div>
          <div>
            <span class="text-white font-bold text-sm">AI 智能助手</span>
            <span class="text-slate-500 text-[10px] ml-2">物理场分析专家 · RAG 增强</span>
          </div>
        </div>
        <!-- 上下文开关 -->
        <div class="flex items-center gap-3">
          <div v-for="(label, key) in { dataset:'数据集', prediction:'预测', model:'模型' }" :key="key"
               class="flex items-center gap-1 cursor-pointer" @click="contextSwitches[key] = !contextSwitches[key]">
            <span class="w-1.5 h-1.5 rounded-full" :class="contextSwitches[key] ? 'bg-green-400' : 'bg-slate-600'"></span>
            <span class="text-[10px]" :class="contextSwitches[key] ? 'text-slate-400' : 'text-slate-600'">{{ label }}</span>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageListRef" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <!-- 欢迎屏幕 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
               style="background:linear-gradient(135deg,rgba(236,72,153,0.1),rgba(139,92,246,0.1)); border:1px solid rgba(236,72,153,0.15);">
            <el-icon size="32" style="color:#f472b6;"><MagicStick /></el-icon>
          </div>
          <h2 class="text-xl font-bold mb-2"
              style="background:linear-gradient(90deg,#f472b6,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            你好，我是物理场 AI 助手
          </h2>
          <p class="text-slate-500 text-sm mb-8 text-center max-w-md">
            我可以帮你分析预测结果、解答电磁学问题、推荐模型参数，也可以直接执行平台操作。
          </p>

          <!-- 预设 Prompt 快捷卡片 -->
          <div class="grid grid-cols-2 gap-3 w-full max-w-lg">
            <div v-for="(p, idx) in presetPrompts" :key="idx"
                 class="prompt-card p-3 rounded-xl cursor-pointer group"
                 @click="handlePreset(p.content)">
              <div class="flex items-center gap-2 mb-1.5">
                <span class="text-base">{{ p.icon }}</span>
                <span class="text-xs font-bold" :style="`color:${p.color}`">{{ p.title }}</span>
              </div>
              <p class="text-[11px] text-slate-500 leading-relaxed group-hover:text-slate-400 transition-colors">{{ p.desc }}</p>
            </div>
          </div>
        </div>

        <!-- 消息气泡 -->
        <template v-for="msg in messages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="flex justify-end gap-3">
            <div class="max-w-[70%]">
              <div class="px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed"
                   style="background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(139,92,246,0.15)); border:1px solid rgba(236,72,153,0.2); color:#e2e8f0;">
                {{ msg.content }}
              </div>
              <div class="text-[10px] text-slate-600 mt-1 text-right">{{ msg.timestamp }}</div>
            </div>
            <div class="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
                 style="background:linear-gradient(135deg,#3b82f6,#8b5cf6); color:white;">U</div>
          </div>

          <!-- AI 消息 -->
          <div v-else class="flex gap-3">
            <div class="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center"
                 style="background:linear-gradient(135deg,#ec4899,#8b5cf6);">
              <el-icon size="13" style="color:#fff;"><MagicStick /></el-icon>
            </div>
            <div class="max-w-[75%] min-w-[200px]">
              <!-- 加载状态 -->
              <div v-if="msg.loading" class="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-bl-md"
                   style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3);">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                <span class="text-slate-500 text-xs">思考中...</span>
              </div>
              <!-- 正常内容 -->
              <div v-else class="px-4 py-3 rounded-2xl rounded-bl-md ai-msg-bubble"
                   :class="msg.error ? 'ai-msg-error' : ''">
                <div class="ai-markdown text-sm leading-relaxed" v-html="renderMarkdown(msg.content)"></div>
              </div>
              <div class="text-[10px] text-slate-600 mt-1">{{ msg.timestamp }}</div>
            </div>
          </div>
        </template>

        <!-- 流式输出时的滚动锚点 -->
        <div ref="scrollAnchorRef"></div>
      </div>

      <!-- 输入区 -->
      <div class="flex-shrink-0 px-5 pb-4 pt-2">
        <!-- 快捷 Prompt 条（对话中也可使用） -->
        <div v-if="messages.length > 0" class="flex gap-2 mb-2 overflow-x-auto pb-1">
          <span v-for="(q, i) in quickActions" :key="i"
                class="quick-chip flex-shrink-0 px-2.5 py-1 rounded-full text-[10px] cursor-pointer"
                @click="handlePreset(q.content)">
            {{ q.icon }} {{ q.label }}
          </span>
        </div>

        <div class="flex items-end gap-3">
          <div class="flex-1 relative">
            <el-input v-model="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 5 }"
                      placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
                      @keydown="handleKeydown" resize="none"
                      class="chat-input" />
          </div>
          <el-button :loading="isStreaming" :disabled="!inputText.trim() || isStreaming"
                     @click="handleSend" circle size="large"
                     style="background:linear-gradient(135deg,#ec4899,#8b5cf6); border:none; width:44px; height:44px;">
            <el-icon size="18" style="color:white;"><Promotion /></el-icon>
          </el-button>
        </div>
        <div class="text-center mt-2">
          <span class="text-[10px] text-slate-700">AI 回答可能存在误差，重要决策请结合专业判断</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import {
  Plus, Close, ChatDotRound, MagicStick, Promotion,
} from '@element-plus/icons-vue';
import { useAiStore } from '../../composables/useAiStore.js';

const {
  conversations, activeConvId, messages, isStreaming,
  newConversation, switchConversation, deleteConversation,
  sendMessage, renderMarkdown, contextSwitches,
} = useAiStore();

const inputText = ref('');
const messageListRef = ref(null);
const scrollAnchorRef = ref(null);

// 预设 Prompt 快捷卡片
const presetPrompts = [
  { icon: '🔍', title: '分析预测结果', desc: '帮我解读最近一次物理场预测的分布特征和异常点', color: '#60a5fa', content: '请分析我最近一次的物理场预测结果，包括分布特征、异常区域和可能的物理含义。' },
  { icon: '⚡', title: '解释磁场分布', desc: '从物理角度解释变压器漏磁场的分布规律', color: '#fbbf24', content: '请从电磁学原理出发，解释变压器漏磁场的空间分布规律，以及影响磁场分布的主要因素。' },
  { icon: '🛠️', title: '推荐模型参数', desc: '根据数据集特征推荐合适的模型架构和超参数', color: '#34d399', content: '请根据我当前数据集的特征（输入维度、输出维度、样本数），推荐合适的神经网络架构和超参数设置。' },
  { icon: '📖', title: 'PCA 降维原理', desc: '解释 PCA 主成分分析在物理场预测中的作用', color: '#c084fc', content: '请解释 PCA 主成分分析的数学原理，以及它在电力设备物理场预测中为什么能有效降低输出维度。' },
];

const quickActions = [
  { icon: '📊', label: '分析损失曲线', content: '当前模型的训练损失曲线是否正常？有没有过拟合或欠拟合的迹象？' },
  { icon: '🔧', label: '调参建议', content: '训练效果不太好，请给我一些超参数调优的建议。' },
  { icon: '📈', label: '对比模型', content: '帮我对比 DNN 和 CNN 在当前物理场预测任务中的优劣。' },
  { icon: '❓', label: '平台使用', content: '请介绍一下这个平台的主要功能模块和使用流程。' },
];

function handlePreset(content) {
  inputText.value = content;
  handleSend();
}

function handleSend() {
  if (!inputText.value.trim() || isStreaming.value) return;
  const text = inputText.value;
  inputText.value = '';
  sendMessage(text);
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

// 自动滚动
watch(
  () => messages.value.length > 0 ? messages.value[messages.value.length - 1]?.content : '',
  () => {
    nextTick(() => {
      scrollAnchorRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  },
  { flush: 'post' }
);

// 如果没有会话则自动创建
onMounted(() => {
  if (conversations.value.length === 0) newConversation();
  else if (!activeConvId.value) switchConversation(conversations.value[0].id);
});
</script>

<style scoped>
.ai-chat-page { height: calc(100vh - 56px); }

/* 会话列表 */
.conv-item:hover { background: rgba(236,72,153,0.05); }
.conv-active { background: rgba(236,72,153,0.1) !important; border-left: 2px solid #ec4899; }

/* Prompt 卡片 */
.prompt-card {
  background: rgba(15,23,42,0.5);
  border: 1px solid rgba(51,65,85,0.3);
  transition: all 0.2s ease;
}
.prompt-card:hover {
  border-color: rgba(236,72,153,0.3);
  background: rgba(15,23,42,0.7);
  transform: translateY(-2px);
}

/* AI 消息气泡 */
.ai-msg-bubble {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.3);
}
.ai-msg-error {
  border-color: rgba(239,68,68,0.3) !important;
  background: rgba(239,68,68,0.06) !important;
}

/* Markdown 样式 */
.ai-markdown :deep(p) { margin: 0.4em 0; color: #cbd5e1; }
.ai-markdown :deep(strong) { color: #f1f5f9; font-weight: 700; }
.ai-markdown :deep(code) {
  background: rgba(59,130,246,0.1); color: #93c5fd; padding: 1px 5px;
  border-radius: 4px; font-size: 0.85em; font-family: 'JetBrains Mono', monospace;
}
.ai-markdown :deep(pre) {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(51,65,85,0.4);
  border-radius: 8px; padding: 12px; margin: 8px 0; overflow-x: auto;
}
.ai-markdown :deep(pre code) { background: none; padding: 0; color: #e2e8f0; }
.ai-markdown :deep(ul), .ai-markdown :deep(ol) { padding-left: 1.2em; margin: 0.4em 0; color: #94a3b8; }
.ai-markdown :deep(li) { margin: 2px 0; }
.ai-markdown :deep(blockquote) {
  border-left: 3px solid rgba(236,72,153,0.4); padding-left: 12px;
  margin: 8px 0; color: #64748b; font-style: italic;
}
.ai-markdown :deep(h1), .ai-markdown :deep(h2), .ai-markdown :deep(h3) {
  color: #e2e8f0; margin: 0.6em 0 0.3em; font-weight: 700;
}
.ai-markdown :deep(table) { border-collapse: collapse; margin: 8px 0; width: 100%; }
.ai-markdown :deep(th), .ai-markdown :deep(td) {
  border: 1px solid rgba(51,65,85,0.4); padding: 6px 10px; font-size: 0.85em;
}
.ai-markdown :deep(th) { background: rgba(15,23,42,0.6); color: #94a3b8; }
.ai-markdown :deep(td) { color: #cbd5e1; }

/* 打字动画 */
.typing-dots { display: flex; gap: 4px; }
.typing-dots span {
  width: 6px; height: 6px; border-radius: 50%;
  background: #64748b; animation: blink 1.4s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

/* 快捷标签 */
.quick-chip {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.3);
  color: #94a3b8;
  transition: all 0.15s;
}
.quick-chip:hover {
  border-color: rgba(236,72,153,0.3);
  color: #f472b6;
  background: rgba(236,72,153,0.06);
}

/* 输入框暗色 */
.chat-input :deep(.el-textarea__inner) {
  background: rgba(15,23,42,0.6) !important;
  border: 1px solid rgba(51,65,85,0.4) !important;
  color: #e2e8f0 !important;
  border-radius: 16px !important;
  padding: 10px 16px !important;
  box-shadow: none !important;
  font-size: 14px;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: rgba(236,72,153,0.4) !important;
}
</style>

