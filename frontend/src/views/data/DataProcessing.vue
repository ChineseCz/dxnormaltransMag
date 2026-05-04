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
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">电磁场工况数据的清洗、划分与特征工程</p>
      </div>
      <button v-if="isTimeDomain" @click="autoDetectStable" :disabled="!activeDataset"
        class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-40"
        style="background:linear-gradient(135deg,#d97706,#f59e0b); border:1px solid rgba(245,158,11,0.4); box-shadow:0 0 16px rgba(217,119,6,0.35);">
        <el-icon><MagicStick /></el-icon>
        自动识别稳态
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

      <!-- Step 1: 稳态截取 / 矩阵装配 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(8,145,178,0.2);">
        <template #header>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded text-xs font-bold text-white flex-shrink-0"
                  style="background:linear-gradient(135deg,#0891b2,#0ea5e9);"></span>
            <span class="text-white font-semibold text-sm">{{ step1Title }}</span>
            <el-tag size="small" effect="plain" style="font-size:10px; margin-left:4px;"
                    :type="dataOrg === 'perfile' ? 'info' : ''">
              {{ dataOrg === 'perfile' ? '逐工况' : dataOrg === 'separated' ? '多通道' : '单文件' }}
            </el-tag>
          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:13px; line-height:1.7;">{{ step1Desc }}</p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">

            <!-- 时域数据集：显示 t₀/tₑ/Δt -->
            <template v-if="isTimeDomain">
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
            </template>

            <!-- 参数化数据集 (multicolumn, no timeStep) -->
            <template v-else-if="dataOrg === 'multicolumn'">
              <div class="flex items-center gap-2 p-3 rounded-lg"
                   style="background:rgba(8,145,178,0.08); border:1px solid rgba(8,145,178,0.25);">
                <el-icon style="color:#22d3ee;" size="14"><InfoFilled /></el-icon>
                <span class="text-cyan-300 text-xs leading-relaxed">
                  当前为<b>参数化稳态</b>数据集，每列对应独立激励工况，
                  平台将直接按工况索引 N 进行矩阵装配，无需时序区间截取。
                </span>
              </div>
            </template>

            <!-- 逐工况模式 (perfile) -->
            <template v-else-if="dataOrg === 'perfile'">
              <div class="flex items-center gap-2 p-3 rounded-lg"
                   style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.25);">
                <el-icon style="color:#a5b4fc;" size="14"><InfoFilled /></el-icon>
                <span class="text-indigo-300 text-xs leading-relaxed">
                  <b>逐工况模式</b>：扫描所有「输出」角色文件，按 conditionValue 升序排列，
                  提取 {{ activeDataset.coordCols }} 列坐标后的场值列，堆叠为工况矩阵。
                  文件名中的数值将作为输入向量。
                </span>
              </div>
            </template>

            <!-- 多文件分离式 (separated) -->
            <template v-else>
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
            </template>

            <div class="flex justify-between items-center">
              <button v-if="isTimeDomain" @click="autoDetectStable" :disabled="!activeDataset"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-all hover:scale-105 disabled:opacity-40"
                style="background:rgba(8,145,178,0.15); border:1px solid rgba(8,145,178,0.3);">
                <el-icon size="12"><MagicStick /></el-icon>自动识别稳态
              </button>
              <div v-else></div>
              <button @click="handleProcess('cut')" :disabled="isProcessing"
                class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 disabled:opacity-50"
                style="background:linear-gradient(135deg,#0891b2,#0ea5e9); border:1px solid rgba(14,165,233,0.4);">
                <el-icon size="14"><Scissor /></el-icon>
                {{ dataOrg === 'perfile' ? '执行逐工况装配' : isTimeDomain ? '执行时域截取' : '执行矩阵装配' }}
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
            基于均匀采样与随机打散，确保训练集、验证集与测试集在
            <span class="text-indigo-300 font-semibold">{{ outputVarName }}</span> 空间拓扑上均具有平衡性。
          </p>
          <div class="p-4 rounded-xl space-y-4" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.5);">

            <!-- 训练集滑块 -->
            <div>
              <div class="flex justify-between text-xs mb-1.5">
                <span class="text-white font-medium">训练集占比 <span class="text-slate-500">(Train)</span></span>
                <span class="text-indigo-400 font-bold font-mono">{{ (processParams.splitRatio * 100).toFixed(0) }}%</span>
              </div>
              <el-slider v-model="processParams.splitRatio"
                         :min="0.5" :max="0.85" :step="0.05"
                         :disabled="processParams.splitRatio + processParams.valRatio >= 0.95"
                         style="--el-slider-main-bg-color:#6366f1;" />
            </div>

            <!-- 验证集滑块 -->
            <div>
              <div class="flex justify-between text-xs mb-1.5">
                <span class="text-white font-medium">验证集占比 <span class="text-slate-500">(Validation)</span></span>
                <span class="text-yellow-400 font-bold font-mono">{{ (processParams.valRatio * 100).toFixed(0) }}%</span>
              </div>
              <el-slider v-model="processParams.valRatio"
                         :min="0.05" :max="0.3" :step="0.05"
                         style="--el-slider-main-bg-color:#eab308;" />
            </div>

            <!-- 三段比例可视化条 -->
            <div class="space-y-1.5">
              <div class="flex rounded-lg overflow-hidden h-5 text-[10px] font-bold font-mono">
                <div class="flex items-center justify-center transition-all duration-300"
                     :style="`width:${(processParams.splitRatio*100).toFixed(0)}%; background:rgba(99,102,241,0.7);`">
                  Train {{ (processParams.splitRatio * 100).toFixed(0) }}%
                </div>
                <div class="flex items-center justify-center transition-all duration-300"
                     :style="`width:${(processParams.valRatio*100).toFixed(0)}%; background:rgba(234,179,8,0.75);`">
                  Val {{ (processParams.valRatio * 100).toFixed(0) }}%
                </div>
                <div class="flex items-center justify-center transition-all duration-300"
                     :style="`width:${(testRatio*100).toFixed(0)}%; background:rgba(16,185,129,0.6);`">
                  Test {{ (testRatio * 100).toFixed(0) }}%
                </div>
              </div>
              <!-- 图例 -->
              <div class="flex items-center gap-4 text-[10px] text-slate-400">
                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm inline-block" style="background:rgba(99,102,241,0.8);"></span>训练集</span>
                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm inline-block" style="background:rgba(234,179,8,0.8);"></span>验证集</span>
                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm inline-block" style="background:rgba(16,185,129,0.8);"></span>测试集</span>
                <span class="ml-auto text-slate-600">合计: 100%</span>
              </div>
            </div>

            <!-- 警告：测试集过小 -->
            <div v-if="testRatio < 0.05"
                 class="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
                 style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); color:#f87171;">
              ⚠ 测试集比例过小（&lt; 5%），请适当减小训练集或验证集占比
            </div>

            <div class="flex justify-end">
              <button @click="handleProcess('split')" :disabled="isProcessing || testRatio < 0.05"
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
            <span class="text-white font-semibold text-sm">电磁场降维分析</span>

          </div>
        </template>
        <div class="space-y-4">
          <p style="color:#e2e8f0; font-size:14px; line-height:1.6;">
            对 当前 <span class="text-purple-300 font-semibold">{{ spatialPoints }}</span> 维
            <span class="text-purple-300">{{ outputVarName }}</span> 空间测点进行主成分提取，将特征空间压缩至核心维度。
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
  splitRatio: 0.7,   // 训练集占比
  valRatio: 0.15,    // 验证集占比
  pcaComponents: 60,
});

// 测试集比例 = 余量（只读）
const testRatio = computed(() =>
  Math.max(0, +(1 - processParams.splitRatio - processParams.valRatio).toFixed(2))
);

// ---- Computed: 动态描述信息 ----
const DEVICE_MAP = { transformer:'变压器', reactor:'电抗器', motor:'电机', gis:'GIS', cable:'电缆', busbar:'母线', other:'其他' };
const FIELD_MAP = { magnetic:'磁场', temperature:'温度场', stress:'应力场', electric:'电场', flow:'流场', other:'电磁场' };
const deviceLabel = computed(() => DEVICE_MAP[activeDataset.value?.deviceType] || '设备');
const fieldLabel = computed(() => FIELD_MAP[activeDataset.value?.fieldType] || '电磁场');
const outputVarName = computed(() => activeDataset.value?.outputVariable?.name || '场量');
const spatialPoints = computed(() => activeDataset.value?.outputVariable?.spatialPoints || '?');

// 数据组织方式
const dataOrg = computed(() => activeDataset.value?.dataOrg || 'multicolumn');
// 是否时域（有timeStep且非perfile）
const isTimeDomain = computed(() => dataOrg.value !== 'perfile' && !!activeDataset.value?.timeStep);
// 坐标系标签
const COORD_SYS_LABEL = { xyz:'x,y,z', rz:'r,z', rphiz:'r,φ,z' };
const coordSysLabel = computed(() => COORD_SYS_LABEL[activeDataset.value?.coordSystem] || activeDataset.value?.coordSystem || '—');

// Step 1 描述（随dataOrg变化）
const step1Title = computed(() => ({
  multicolumn: '时域工况截取 → 矩阵构建',
  perfile:     '逐工况文件扫描 → 矩阵装配',
  separated:   '多通道时域截取 → 矩阵构建',
}[dataOrg.value] || '工况-空间矩阵构建'));

const step1Desc = computed(() => {
  const ds = activeDataset.value;
  if (!ds) return '';
  if (dataOrg.value === 'perfile') {
    const n = ds.outputVariable?.conditionCount || ds.files?.filter(f => f.role === 'output').length || 0;
    return `逐工况模式：扫描 ${n} 个工况文件（坐标系 ${coordSysLabel.value}），按文件名中提取的激励量值排序，装配为 N工况 × M空间点 输出矩阵，文件名数值自动作为输入标量。`;
  } else if (dataOrg.value === 'separated') {
    const nIn = (ds.inputVariables || []).length;
    return `多文件分离式：截取时间区间 [t₀, tₑ] 内的稳态数据，从 ${nIn} 个独立输入激励文件和输出场文件中同步提取，构建多通道工况矩阵（坐标系 ${coordSysLabel.value}）。`;
  } else {
    return `时域多时步：从单个输出场文件（坐标系 ${coordSysLabel.value}）中截取稳态区间，提取各时间步的空间场分布。同步从各输入激励量文件中截取对应时段。`;
  }
});

const inputVarSummary = computed(() => {
  if (dataOrg.value === 'perfile') return '文件名中提取的激励量标量（自动）';
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
    processParams.splitRatio = ds.processConfig.splitRatio ?? 0.7;
    processParams.valRatio = ds.processConfig.valRatio ?? 0.15;
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
  const labels = {
    cut: isTimeDomain.value ? '时域工况切分' : '工况矩阵装配',
    split: '训练/验证/测试集划分',
    normalize: '归一化处理',
    pca: 'PCA 降维训练'
  };
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
