<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- 页面标题 -->
    <div class="px-6 pt-6 pb-4">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#f59e0b,#b45309); box-shadow:0 0 20px rgba(245,158,11,0.4);">
            <el-icon size="20" style="color:#fff;"><Clock /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            预测记录
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">浏览、查看、对比过往预测历史</p>
      </div>
    </div>

    <div class="px-6 pb-6 space-y-5">
      <!-- 顶部工具栏 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-slate-400 text-sm font-semibold">
            共 <span class="text-amber-400 font-bold">{{ history.length }}</span> 条记录
          </span>
          <el-input v-model="searchText" size="small" placeholder="搜索模型/数据集..."
                    clearable style="width:200px;" prefix-icon="Search" />
        </div>
        <el-button v-if="history.length > 0" type="danger" plain size="small" @click="handleClear">
          <el-icon class="mr-1"><Delete /></el-icon>清空全部
        </el-button>
      </div>

      <!-- 记录列表 -->
      <TransitionGroup name="list" tag="div" class="space-y-3">
        <div v-for="(record, idx) in filteredHistory" :key="record.id"
             class="history-item group">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold"
                 :style="`background:${indexColors[idx % indexColors.length]}15; color:${indexColors[idx % indexColors.length]};`">
              {{ idx + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <el-tag size="small" :type="modelTagType(record.modelType)" effect="dark" round>{{ record.modelType }}</el-tag>
                <span class="text-white text-sm font-semibold truncate">{{ record.modelFile }}</span>
              </div>
              <div class="flex items-center gap-3 text-[11px] text-slate-500">
                <span class="flex items-center gap-1"><el-icon size="11"><Clock /></el-icon>{{ record.timestamp }}</span>
                <span class="flex items-center gap-1"><el-icon size="11"><Folder /></el-icon>{{ record.datasetName || '—' }}</span>
                <span class="flex items-center gap-1"><el-icon size="11"><DataLine /></el-icon>{{ (record.fieldValues || []).length }} 场点</span>
              </div>
              <div class="flex flex-wrap gap-1.5 mt-2">
                <span v-for="(val, key) in limitedInputs(record.inputs)" :key="key"
                      class="px-2 py-0.5 rounded text-[10px] font-mono"
                      style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3); color:#94a3b8;">
                  {{ key }}=<span class="text-blue-400">{{ typeof val === 'number' ? val.toFixed(2) : val }}</span>
                </span>
              </div>
              <div v-if="record.fieldValues?.length" class="flex items-center gap-4 mt-2 text-[10px]">
                <span class="text-slate-600">min: <span class="text-cyan-400 font-mono">{{ fieldMin(record).toExponential(2) }}</span></span>
                <span class="text-slate-600">max: <span class="text-pink-400 font-mono">{{ fieldMax(record).toExponential(2) }}</span></span>
                <span class="text-slate-600">mean: <span class="text-purple-400 font-mono">{{ fieldMean(record).toExponential(2) }}</span></span>
              </div>
            </div>
            <div class="flex-shrink-0 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <el-tooltip content="查看结果" placement="top">
                <el-button size="small" circle
                           style="background:rgba(59,130,246,0.1); border-color:rgba(59,130,246,0.3); color:#60a5fa;"
                           @click="viewRecord(record)">
                  <el-icon size="14"><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="加入对比" placement="top">
                <el-button size="small" circle
                           style="background:rgba(168,85,247,0.1); border-color:rgba(168,85,247,0.3); color:#c084fc;"
                           @click="goCompare()">
                  <el-icon size="14"><Switch /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除记录" placement="top">
                <el-button size="small" circle
                           style="background:rgba(239,68,68,0.1); border-color:rgba(239,68,68,0.3); color:#f87171;"
                           @click="handleDelete(record)">
                  <el-icon size="14"><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </TransitionGroup>

      <!-- 空状态 -->
      <div v-if="filteredHistory.length === 0" class="flex flex-col items-center justify-center py-24">
        <div class="w-20 h-20 rounded-2xl flex items-center justify-center mb-4"
             style="background:rgba(245,158,11,0.05); border:1px solid rgba(245,158,11,0.1);">
          <el-icon size="40" style="color:#292524;"><Clock /></el-icon>
        </div>
        <p class="text-slate-600 text-sm font-medium">暂无预测记录</p>
        <p class="text-slate-700 text-xs mt-1">完成一次预测后，记录将自动保存在此</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { Clock, Delete, View, Folder, Switch, DataLine } from '@element-plus/icons-vue';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

const {
  predictionHistory: history,
  viewRecord,
  deleteRecord,
  clearHistory,
  goCompare,
} = usePredictionStore();

const searchText = ref('');
const indexColors = ['#60a5fa', '#c084fc', '#34d399', '#fbbf24', '#f472b6', '#fb923c'];

function modelTagType(type) {
  const map = { DNN: '', CNN: 'warning', LSTM: 'success', SVM: 'info', RF: 'danger' };
  return map[type] || 'info';
}

const filteredHistory = computed(() => {
  if (!searchText.value) return history.value;
  const q = searchText.value.toLowerCase();
  return history.value.filter(r =>
    (r.modelFile || '').toLowerCase().includes(q) ||
    (r.datasetName || '').toLowerCase().includes(q) ||
    (r.modelType || '').toLowerCase().includes(q)
  );
});

function limitedInputs(inputs) {
  if (!inputs) return {};
  return Object.fromEntries(Object.entries(inputs).slice(0, 6));
}

function fieldMin(r) { return Math.min(...(r.fieldValues || [0])); }
function fieldMax(r) { return Math.max(...(r.fieldValues || [0])); }
function fieldMean(r) {
  const fv = r.fieldValues || [];
  return fv.length ? fv.reduce((a, b) => a + b, 0) / fv.length : 0;
}

function handleDelete(record) {
  ElMessageBox.confirm(
    `确定删除此预测记录吗？\n${record.timestamp} | ${record.modelType}`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  ).then(() => {
    deleteRecord(record.id);
    ElMessage.success('记录已删除');
  }).catch(() => {});
}

function handleClear() {
  ElMessageBox.confirm(
    '确定清空所有预测历史记录？此操作不可恢复。',
    '清空确认',
    { type: 'error', confirmButtonText: '清空', cancelButtonText: '取消' }
  ).then(() => {
    clearHistory();
    ElMessage.success('历史记录已清空');
  }).catch(() => {});
}
</script>

<style scoped>
.history-item {
  padding: 16px 20px;
  border-radius: 14px;
  border: 1px solid rgba(51,65,85,0.3);
  background: linear-gradient(135deg, rgba(15,23,42,0.5) 0%, rgba(15,23,42,0.3) 100%);
  transition: all 0.2s ease;
}
.history-item:hover {
  border-color: rgba(245,158,11,0.25);
  background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.3) 100%);
}
.list-enter-active, .list-leave-active { transition: all 0.4s ease; }
.list-enter-from { opacity: 0; transform: translateY(-12px); }
.list-leave-to { opacity: 0; transform: translateX(30px); }
.list-move { transition: transform 0.4s ease; }
</style>
