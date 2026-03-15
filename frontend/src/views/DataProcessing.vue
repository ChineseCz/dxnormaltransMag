<template>
  <div class="p-6 space-y-6 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-3">
        <img src="/logo.svg" alt="logo" style="width:28px; height:28px; flex-shrink:0;" />
        <div>
          <div class="section-badge mb-1">
            <span style="width:6px;height:6px;background:#22d3ee;border-radius:50%;display:inline-block;"></span>
            Data Processing
          </div>
          <h1 class="text-lg font-bold text-white tracking-tight leading-tight">数据治理与稳态特征提取</h1>
          <p class="text-slate-400 text-xs mt-0.5">电参量时序数据的清洗、划分与特征工程</p>
        </div>
      </div>
      <button @click="autoDetectStable"
        class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#d97706,#f59e0b); border:1px solid rgba(245,158,11,0.4); box-shadow:0 0 16px rgba(217,119,6,0.35);">
        <el-icon><MagicStick /></el-icon>
        一键识别稳态起点
      </button>
    </div>

    <!-- 4 Step Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">

      <!-- Step 1 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(8,145,178,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#0891b2,#0ea5e9);">1</span>
            <span class="text-white font-semibold text-sm">. 稳态周期自动截取</span>
            <span class="text-slate-400 text-xs ml-1">· Cut & Split</span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            利用 FFT 算法或相关性分析，消除仿真初始阶段的暂态涌流干扰，自动提取稳定运行区间。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <div class="text-xs text-white mb-1.5 font-medium">推荐起始时刻 (t0)</div>
                <el-input-number v-model="processParams.t0" :precision="4" :step="0.0005" size="small" class="w-full" controls-position="right" />
              </div>
              <div>
                <div class="text-xs text-white mb-1.5 font-medium">采样步长 (Δt)</div>
                <el-input v-model="processParams.dt" size="small" disabled placeholder="5e-4" />
              </div>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('split')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#0891b2,#0ea5e9); border:1px solid rgba(14,165,233,0.4);">
                <el-icon size="14"><Scissor /></el-icon>执行物理步长切分
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 2 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#4f46e5,#818cf8);">2</span>
            <span class="text-white font-semibold text-sm">. 数据集拓扑划分</span>
            <span class="text-slate-400 text-xs ml-1">· Topology Partition</span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            基于均匀采样与随机打散，确保训练集与测试集在磁场空间拓扑上具有平衡性。
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
              <button @click="handleProcess('partition')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#4f46e5,#818cf8); border:1px solid rgba(99,102,241,0.4);">
                <el-icon size="14"><Share /></el-icon>同步划分索引
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 3 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(16,185,129,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#059669,#10b981);">3</span>
            <span class="text-white font-semibold text-sm">. 特征归一化与尺度变换</span>
            <span class="text-slate-400 text-xs ml-1">· Z-Score Normalization</span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            对电参量（kV/A）与磁感应强度（T）进行 Z-Score 映射，通过存储统计算子确保在线预测的一致性。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="flex items-center gap-2 p-2.5 rounded-lg" style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2);">
              <el-icon style="color:#34d399;" size="14"><InfoFilled /></el-icon>
              <span class="text-emerald-300 text-xs font-mono">检测到物理单位：Voltage:V, Current:A, B:Tesla</span>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('normalize')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#059669,#10b981); border:1px solid rgba(16,185,129,0.4);">
                <el-icon size="14"><Odometer /></el-icon>计算统计算子 (Mu/Sigma)
              </button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Step 4 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(168,85,247,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#7c3aed,#a855f7);">4</span>
            <span class="text-white font-semibold text-sm">. 高维场降维分析</span>
            <span class="text-slate-400 text-xs ml-1">· Field PCA</span>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            对 1241 维空间测点进行主成分提取，在保障 99%+ 方差覆盖的前提下，将特征空间压缩至核心维度。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">
            <div class="flex items-center gap-4">
              <div class="flex-1">
                <div class="text-xs text-white mb-1.5 font-medium">主成分节点数</div>
                <el-input-number v-model="processParams.pcaNodes" :min="1" :max="200" size="small" class="w-full" controls-position="right" />
              </div>
              <div class="text-center">
                <div class="text-xs text-slate-400 mb-1">预估解释度</div>
                <div class="text-purple-300 font-bold font-mono text-sm">99.8%</div>
              </div>
            </div>
            <div class="flex justify-end">
              <button @click="handleProcess('pca')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#7c3aed,#a855f7); border:1px solid rgba(168,85,247,0.4);">
                <el-icon size="14"><DataAnalysis /></el-icon>拟合投影矩阵
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
import { ref, reactive } from 'vue';
import { Scissor, Share, Odometer, MagicStick, InfoFilled, DataAnalysis, Monitor } from '@element-plus/icons-vue';
import { ElNotification, ElMessage } from 'element-plus';

const isProcessing = ref(false);
const processLogs = ref([]);

const processParams = reactive({
  t0: 0.0400,
  dt: 5e-4,
  splitRatio: 0.8,
  pcaNodes: 60
});

const addLog = (msg) => {
  const time = new Date().toLocaleTimeString();
  processLogs.value.unshift({ time, msg });
};

const autoDetectStable = async () => {
  addLog("正在启动自适应稳态识别算法 (RMSE-based)...");
  try {
    const response = await fetch('http://127.0.0.1:5000/api/data/auto-detect', { method: 'POST' });
    const data = await response.json();
    if (data.t0 !== undefined) {
      processParams.t0 = data.t0;
      addLog(`识别成功：${data.suggested_msg}`);
      ElMessage.success("已自动提取稳态起始时间");
    } else {
      addLog(`算法识别异常: ${data.error || '提取失败'}`);
      ElMessage.error("识别失败，请确保已上传电参量原始数据");
    }
  } catch (error) {
    addLog(`算法识别异常: ${error.message}`);
    ElMessage.error("识别失败，请确保已上传电参量原始数据");
  }
};

const handleProcess = async (type) => {
  isProcessing.value = true;
  const labels = { split: '数据截取与切分', partition: '训练/测试集划分', normalize: '归一化处理', pca: 'PCA 降维训练' };
  addLog(`同步后端执行: ${labels[type]}...`);
  try {
    const response = await fetch('http://127.0.0.1:5000/api/data/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, params: processParams })
    });
    const result = await response.json();
    if (result.status === 'success') {
      addLog(`${labels[type]} 执行完成: ${result.msg}`);
      ElNotification({ title: '处理成功', message: result.msg, type: 'success' });
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
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
