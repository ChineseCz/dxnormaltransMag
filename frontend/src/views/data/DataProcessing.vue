<template>
  <div class="p-6 space-y-6 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#d97706,#f59e0b); box-shadow:0 0 20px rgba(217,119,6,0.4);">
            <el-icon size="20" style="color:white;"><MagicStick /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#fbbf24,#fcd34d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            数据治理与特征提取
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">电参量时序数据的清洗、划分与特征工程</p>
      </div>
      <button @click="autoDetectStable" :disabled="!activeDataset"
        class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-40"
        style="background:linear-gradient(135deg,#d97706,#f59e0b); border:1px solid rgba(245,158,11,0.4); box-shadow:0 0 16px rgba(217,119,6,0.35);">
        <el-icon><MagicStick /></el-icon>
        数据流水线一键处理
      </button>
    </div>

    <!-- Dataset Selector Bar -->
    <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <DatasetSelector ref="selectorRef" @change="onDatasetChange" />
      <p v-if="!activeDataset" class="text-yellow-500/80 text-xs mt-2">
        ⚠ 请先选择一个数据集以开始数据处理流程
      </p>
    </div>

    <!-- 4 Step Cards -->
    <div v-if="activeDataset" class="grid grid-cols-1 md:grid-cols-2 gap-5">

      <!-- Step 1: 稳态截取 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(8,145,178,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#0891b2,#0ea5e9);"></span>
            <span class="text-white font-semibold text-sm">时空矩阵数据集构建</span>
            <span class="text-slate-400 text-xs ml-1"></span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            从 <span class="text-cyan-300 font-semibold">{{ deviceLabel }}</span> 的
            <span class="text-cyan-300 font-semibold">{{ fieldLabel }}</span>仿真数据中，
            提取稳定运行区间，并构建时空矩阵数据集。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="grid grid-cols-3 gap-4">
              <div>
                <div class="text-xs text-white mb-1.5 font-medium">起始时刻 t₀ (s)</div>
                <el-input-number v-model="processParams.t0" :precision="4" :step="0.001" size="small" class="w-full" controls-position="right" />
              </div>
              <div>
                <div class="text-xs text-white mb-1.5 font-medium">结束时刻 tₑ (s)</div>
                <el-input-number v-model="processParams.tEnd" :precision="4" :step="0.01" size="small" class="w-full" controls-position="right" />
              </div>
              <div>
                <div class="text-xs text-white mb-1.5 font-medium">采样步长 Δt (s)</div>
                <el-input v-model="processParams.dt" size="small" disabled />
              </div>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('cut')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#0891b2,#0ea5e9); border:1px solid rgba(14,165,233,0.4);">
                <el-icon size="14"><Scissor /></el-icon>执行物理步长切分
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 2: 数据划分 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#4f46e5,#818cf8);"></span>
            <span class="text-white font-semibold text-sm">数据集拓扑划分</span>

          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            基于均匀采样与随机打散，确保训练集与测试集在
            <span class="text-indigo-300 font-semibold">{{ outputVarName }}</span>空间 拓扑上具有平衡性。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div>
              <div class="flex justify-between text-xs mb-2">
                <span class="text-white font-medium">训练集占比 (Train Ratio)</span>
                <span class="text-indigo-400 font-bold font-mono">{{ (processParams.splitRatio * 100).toFixed(0) }}%</span>
              </div>
              <el-slider v-model="processParams.splitRatio" :min="0.1" :max="0.9" :step="0.05"
                         style="--el-slider-main-bg-color:#6366f1;" />
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('split')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#4f46e5,#818cf8); border:1px solid rgba(99,102,241,0.4);">
                <el-icon size="14"><Share /></el-icon>同步划分索引
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 3: 归一化 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(16,185,129,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#059669,#10b981);"></span>
            <span class="text-white font-semibold text-sm">数据标准化</span>
            <span class="text-slate-400 text-xs ml-1">· Z-Score Normalization</span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            对输入激励量进行 Z-Score 映射，通过存储统计算子 (μ, σ) 确保在线预测的一致性。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="flex items-center gap-2 p-2.5 rounded-lg" style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2);">
              <el-icon style="color:#34d399;" size="14"><InfoFilled /></el-icon>
              <span class="text-emerald-300 text-xs font-mono">
                检测到输入变量：{{ inputVarSummary }}
              </span>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('normalize')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#059669,#10b981); border:1px solid rgba(16,185,129,0.4);">
                <el-icon size="14"><Odometer /></el-icon>标准化 (μ/σ)
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 4: PCA 降维 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(168,85,247,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#7c3aed,#a855f7);"></span>
            <span class="text-white font-semibold text-sm">物理场场降维分析</span>

          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            对 当前 1241 维
            <span class="text-purple-300">{{ outputVarName }}</span>空间测点进行主成分提取，将特征空间压缩至核心维度。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="flex items-center gap-4">
              <div class="flex-1">
                <div class="text-xs text-white mb-1.5 font-medium">主成分数</div>
                <el-input-number v-model="processParams.pcaComponents" :min="1" :max="500" size="small" class="w-full" controls-position="right" />
              </div>
              <div class="text-center">
                <div class="text-xs text-slate-400 mb-1">目标压缩</div>
                <div class="text-purple-300 font-bold font-mono text-sm">
                  {{ spatialPoints }} → {{ processParams.pcaComponents }}
                </div>
              </div>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('pca')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#7c3aed,#a855f7); border:1px solid rgba(168,85,247,0.4);">
                <el-icon size="14"><DataAnalysis /></el-icon>执行降维算子
              </button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Status Console -->
    <el-card style="background:#020817; border:1px solid rgba(51,65,85,0.5);">
      <template #header>
        <div class="flex items-center gap-2">
          <el-icon style="color:#22d3ee;" size="13"><Monitor /></el-icon>
          <span class="font-mono text-xs text-emerald-400">Processing Console</span>
        </div>
      </template>
      <div class="h-36 overflow-y-auto font-mono text-xs space-y-1 custom-scrollbar">
        <div v-for="(log, index) in processLogs" :key="index">
          <span class="text-slate-600">[{{ log.time }}]</span>
          <span class="text-emerald-400 ml-2">{{ log.msg }}</span>
        </div>
        <div v-if="processLogs.length === 0" class="text-slate-600 italic">等待操作控制台输出...</div>
      </div>
    </el-card>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { Scissor, Share, Odometer, MagicStick, InfoFilled, DataAnalysis, Monitor } from '@element-plus/icons-vue';
import { ElNotification, ElMessage } from 'element-plus';
import DatasetSelector from '../../components/DatasetSelector.vue';

const API = 'http://127.0.0.1:5000/api/dataset';

const selectorRef = ref(null);
const activeDataset = ref(null);
const isProcessing = ref(false);
const processLogs = ref([]);

const processParams = reactive({
  t0: 0.04,
  tEnd: 0.1,
  dt: '5e-4',
  splitRatio: 0.8,
  pcaComponents: 60,
});

// ---- Computed: 动态描述信息 ----
const DEVICE_MAP = { transformer:'变压器', reactor:'电抗器', motor:'电机', gis:'GIS', cable:'电缆', busbar:'母线', other:'其他' };
const FIELD_MAP = { magnetic:'磁场', temperature:'温度场', stress:'应力场', electric:'电场', flow:'流场', other:'物理场' };
const deviceLabel = computed(() => DEVICE_MAP[activeDataset.value?.deviceType] || '设备');
const fieldLabel = computed(() => FIELD_MAP[activeDataset.value?.fieldType] || '物理场');
const outputVarName = computed(() => activeDataset.value?.outputVariable?.name || '场量');
const spatialPoints = computed(() => activeDataset.value?.outputVariable?.spatialPoints || '?');

const inputVarSummary = computed(() => {
  const vars = activeDataset.value?.inputVariables || [];
  if (vars.length === 0) return '无输入变量定义';
  return vars.map(v => `${v.name}:${v.unit}`).join(', ');
});

function onDatasetChange(ds) {
  activeDataset.value = ds;
  if (ds?.processConfig) {
    processParams.t0 = ds.processConfig.t0 ?? 0.04;
    processParams.tEnd = ds.processConfig.tEnd ?? 0.1;
    processParams.dt = String(ds.processConfig.dt ?? ds.timeStep ?? 5e-4);
    processParams.splitRatio = ds.processConfig.splitRatio ?? 0.8;
    processParams.pcaComponents = ds.processConfig.pcaComponents ?? 60;
  }
  addLog(`已切换数据集：${ds?.name || '无'}`);
}

const addLog = (msg) => {
  processLogs.value.unshift({ time: new Date().toLocaleTimeString(), msg });
};

const autoDetectStable = async () => {
  if (!activeDataset.value) return;
  addLog("正在启动自适应稳态识别算法...");
  try {
    const r = await fetch(`${API}/${activeDataset.value.id}/auto-detect`, { method: 'POST' });
    const data = await r.json();
    if (data.t0 !== undefined) {
      processParams.t0 = data.t0;
      addLog(`识别成功：${data.suggested_msg}`);
      ElMessage.success("已自动提取稳态起始时间");
    } else {
      addLog(`识别异常: ${data.error || '提取失败'}`);
      ElMessage.error("识别失败");
    }
  } catch (error) {
    addLog(`识别异常: ${error.message}`);
    ElMessage.error("识别失败，请确保后端服务运行中");
  }
};

const handleProcess = async (step) => {
  if (!activeDataset.value) return;
  isProcessing.value = true;
  const labels = { cut: '数据截取与切分', split: '训练/测试集划分', normalize: '归一化处理', pca: 'PCA 降维训练' };
  addLog(`同步后端执行: ${labels[step]}...`);
  try {
    const r = await fetch(`${API}/${activeDataset.value.id}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step, params: processParams }),
    });
    const result = await r.json();
    if (result.status === 'success') {
      addLog(`${labels[step]} 执行完成: ${result.msg}`);
      ElNotification({ title: '处理成功', message: result.msg, type: 'success' });
      // 刷新数据集元信息
      await refreshDataset();
    } else {
      addLog(`执行出错: ${result.error || '处理失败'}`);
      ElNotification({ title: '执行失败', message: result.error || '处理失败', type: 'error' });
    }
  } catch (error) {
    addLog(`执行出错: ${error.message}`);
    ElNotification({ title: '执行失败', message: `处理出错: ${error.message}`, type: 'error' });
  } finally {
    isProcessing.value = false;
  }
};

async function refreshDataset() {
  if (!activeDataset.value) return;
  try {
    const r = await fetch(`${API}/${activeDataset.value.id}`);
    const d = await r.json();
    activeDataset.value = d.dataset;
  } catch { /* ignore */ }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
