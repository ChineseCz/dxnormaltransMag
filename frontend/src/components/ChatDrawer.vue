<template>
  <!-- 悬浮按钮 -->
  <div class="fixed bottom-8 right-8 z-50">
    <el-button circle @click="openDrawer"
      style="width:52px;height:52px;background:linear-gradient(135deg,#ec4899,#8b5cf6);border:none;box-shadow:0 0 28px rgba(236,72,153,0.4);">
      <el-icon size="22" style="color:white;"><ChatDotRound /></el-icon>
    </el-button>
  </div>

  <!-- 抽屉 -->
  <el-drawer v-model="drawerVisible" direction="rtl" size="420px" :with-header="false"
             style="--el-drawer-bg-color:#0a1020;">
    <div class="flex flex-col h-full">
      <!-- 头部 -->
      <div class="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b"
           style="border-color:rgba(51,65,85,0.3);">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg flex items-center justify-center"
               style="background:linear-gradient(135deg,#ec4899,#8b5cf6);">
            <el-icon size="13" style="color:#fff;"><MagicStick /></el-icon>
          </div>
          <span class="text-white font-bold text-sm">AI 快捷助手</span>
        </div>
        <div class="flex items-center gap-1">
          <el-tooltip content="在完整页面中打开" placement="left">
            <el-button size="small" text circle style="color:#64748b;" @click="expandDrawerToFull">
              <el-icon size="14"><FullScreen /></el-icon>
            </el-button>
          </el-tooltip>
          <el-button size="small" text circle style="color:#64748b;" @click="closeDrawer">
            <el-icon size="14"><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="drawerMsgRef" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        <!-- 欢迎 -->
        <div v-if="drawerMessages.length === 0" class="text-center py-8">
          <el-icon size="32" style="color:#334155;"><MagicStick /></el-icon>
          <p class="text-slate-500 text-xs mt-2">有什么我可以帮你的？</p>
          <!-- 快捷提问 -->
          <div class="space-y-2 mt-4">
            <div v-for="(q, i) in quickQuestions" :key="i"
                 class="px-3 py-2 rounded-lg text-left cursor-pointer text-xs transition-all"
                 style="background:rgba(15,23,42,0.5); border:1px solid rgba(51,65,85,0.3); color:#94a3b8;"
                 @click="handleQuickQ(q)" @mouseenter="$event.target.style.borderColor='rgba(236,72,153,0.3)'"
                 @mouseleave="$event.target.style.borderColor='rgba(51,65,85,0.3)'">
              {{ q }}
            </div>
          </div>
        </div>

        <!-- 消息 -->
        <template v-for="msg in drawerMessages" :key="msg.id">
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="max-w-[85%] px-3 py-2 rounded-xl rounded-br-sm text-xs leading-relaxed"
                 style="background:rgba(236,72,153,0.12); border:1px solid rgba(236,72,153,0.2); color:#e2e8f0;">
              {{ msg.content }}
            </div>
          </div>
          <div v-else class="flex gap-2">
            <div class="w-6 h-6 rounded-md flex-shrink-0 flex items-center justify-center"
                 style="background:linear-gradient(135deg,#ec4899,#8b5cf6);">
              <el-icon size="10" style="color:#fff;"><MagicStick /></el-icon>
            </div>
            <div class="max-w-[85%]">
              <div v-if="msg.loading" class="flex items-center gap-2 px-3 py-2 rounded-xl rounded-bl-sm"
                   style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3);">
                <div class="typing-dots"><span></span><span></span><span></span></div>
              </div>
              <div v-else class="px-3 py-2 rounded-xl rounded-bl-sm text-xs leading-relaxed drawer-md"
                   style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3);"
                   v-html="renderMarkdown(msg.content)">
              </div>
            </div>
          </div>
        </template>
        <div ref="drawerAnchorRef"></div>
      </div>

      <!-- 输入 -->
      <div class="flex-shrink-0 px-4 py-3 border-t" style="border-color:rgba(51,65,85,0.3);">
        <div class="flex gap-2">
          <el-input v-model="drawerInput" size="default" placeholder="快速提问..."
                    @keydown.enter="handleDrawerSend" class="drawer-input" />
          <el-button :loading="isDrawerStreaming" :disabled="!drawerInput.trim()" circle
                     @click="handleDrawerSend"
                     style="background:linear-gradient(135deg,#ec4899,#8b5cf6); border:none; width:36px; height:36px;">
            <el-icon size="14" style="color:white;"><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import {
  ChatDotRound, MagicStick, Close, FullScreen, Promotion,
} from '@element-plus/icons-vue';
import { useAiStore } from '../composables/useAiStore.js';

const {
  drawerVisible, drawerMessages, isDrawerStreaming,
  openDrawer, closeDrawer, sendDrawerMessage, expandDrawerToFull,
  renderMarkdown,
} = useAiStore();

const drawerInput = ref('');
const drawerMsgRef = ref(null);
const drawerAnchorRef = ref(null);

const quickQuestions = [
  '📖 这个平台怎么用？',
  '🔧 如何上传数据并训练模型？',
  '📊 预测结果怎么解读？',
  '⚡ 帮我推荐模型参数',
];

function handleQuickQ(q) {
  drawerInput.value = q;
  handleDrawerSend();
}

function handleDrawerSend() {
  if (!drawerInput.value.trim() || isDrawerStreaming.value) return;
  const text = drawerInput.value;
  drawerInput.value = '';
  sendDrawerMessage(text);
}

// 自动滚动
watch(
  () => drawerMessages.value.length > 0 ? drawerMessages.value[drawerMessages.value.length - 1]?.content : '',
  () => { nextTick(() => { drawerAnchorRef.value?.scrollIntoView({ behavior: 'smooth' }); }); },
  { flush: 'post' }
);
</script>

<style scoped>
.typing-dots { display: flex; gap: 3px; }
.typing-dots span {
  width: 5px; height: 5px; border-radius: 50%;
  background: #64748b; animation: blink 1.4s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

.drawer-md :deep(p) { margin: 0.3em 0; color: #cbd5e1; }
.drawer-md :deep(code) { background: rgba(59,130,246,0.1); color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-size: 0.85em; }
.drawer-md :deep(strong) { color: #f1f5f9; }
.drawer-md :deep(ul), .drawer-md :deep(ol) { padding-left: 1em; color: #94a3b8; }

.drawer-input :deep(.el-input__wrapper) {
  background: rgba(15,23,42,0.6) !important;
  border: 1px solid rgba(51,65,85,0.4) !important;
  box-shadow: none !important;
  border-radius: 10px !important;
}
.drawer-input :deep(.el-input__inner) { color: #e2e8f0 !important; font-size: 13px; }
</style>

