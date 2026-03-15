<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#2563eb,#4f46e5); box-shadow:0 0 20px rgba(59,130,246,0.4);">
            <el-icon size="20" style="color:white;"><VideoPlay /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#60a5fa,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            模型训练任务调度
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">深度学习 / 机器学习模型训练过程管理与实时监控</p>
      </div>
      <button @click="reloadConfig"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
              style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.3); color:#e2e8f0;">
        <el-icon><Refresh /></el-icon>
        同步架构配置
      </button>
    </div>

    <!-- Dataset Selector Bar -->
    <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <DatasetSelector ref="dsSelectorRef" @change="onDatasetChange" />
    </div>

    <!-- Active Model Summary Bar -->
    <div class="p-4 rounded-xl flex items-center gap-4 flex-wrap"
         :style="`background:${currentModel.activeBg}; border:1px solid ${currentModel.borderColor};`">
      <div class="flex items-center gap-3 flex-shrink-0">
        <div class="w-10 h-10 rounded-xl flex items-center justify-center"
             :style="`background:${currentModel.iconBgActive};`">
          <el-icon size="20" :style="`color:${currentModel.color};`"><component :is="currentModel.icon" /></el-icon>
        </div>
        <div>
          <div class="text-[10px] text-slate-500 mb-0.5 uppercase tracking-widest">当前训练架构</div>
          <div class="font-bold text-sm tracking-wide" :style="`color:${currentModel.color}`">
            {{ currentModel.label }} Model
          </div>
        </div>
      </div>
      <div class="w-px h-10 flex-shrink-0" style="background:rgba(51,65,85,0.6);"></div>
      <!-- DL params chips -->
      <template v-if="isDLModel">
        <div class="config-chip">优化器 <span>{{ savedConfig.dlParams?.optimizer || 'Adam' }}</span></div>
        <div class="config-chip">学习率 <span>{{ savedConfig.dlParams?.lr || '1e-4' }}</span></div>
        <div class="config-chip">Batch <span>{{ savedConfig.dlParams?.batchSize || 16 }}</span></div>
        <div class="config-chip">Epochs <span>{{ totalEpochs }}</span></div>
        <div v-if="modelType === 'dnn'" class="config-chip">层结构 <span>{{ dnnLayerStr }}</span></div>
        <div v-if="modelType === 'cnn'" class="config-chip">卷积块 <span>{{ savedConfig.cnn?.convLayers?.length || 2 }} Conv1D</span></div>
        <div v-if="modelType === 'lstm'" class="config-chip">LSTM层 <span>{{ savedConfig.lstm?.layers?.length || 2 }} 层</span></div>
      </template>
      <!-- ML params chips -->
      <template v-if="!isDLModel">
        <template v-if="modelType === 'svm'">
          <div class="config-chip">核函数 <span>{{ savedConfig.svm?.kernel?.toUpperCase() || 'RBF' }}</span></div>
          <div class="config-chip">C <span>{{ savedConfig.svm?.C || 1.0 }}</span></div>
          <div class="config-chip">ε <span>{{ savedConfig.svm?.epsilon || 0.1 }}</span></div>
        </template>
        <template v-if="modelType === 'rf'">
          <div class="config-chip">Trees <span>{{ savedConfig.rf?.nEstimators || 100 }}</span></div>
          <div class="config-chip">MaxDepth <span>{{ savedConfig.rf?.maxDepth || 20 }}</span></div>
        </template>
        <div class="config-chip">K-Fold <span>{{ savedConfig.mlParams?.cvFolds || 5 }}-Fold</span></div>
        <div class="config-chip">指标 <span>MAE</span></div>
      </template>
      <div class="ml-auto flex-shrink-0">
        <span class="text-xs px-3 py-1.5 rounded-full font-semibold"
              :style="`background:${currentModel.iconBg}; color:${currentModel.color}; border:1px solid ${currentModel.borderColor};`">
          {{ isDLModel ? 'GPU 加速训练' : 'CPU 多核并行' }}
        </span>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- Control Panel -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(59,130,246,0.15);">
        <template #header>
          <div class="flex items-center gap-2">
            <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(59,130,246,0.2);">
              <el-icon style="color:#60a5fa;" size="13"><VideoPlay /></el-icon>
            </div>
            <span class="text-slate-200 font-semibold text-sm">训练控制面板</span>
            <div class="ml-auto">
              <span v-if="training" class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full"
                    style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
                运行中
              </span>
              <span v-else class="text-xs px-2 py-0.5 rounded-full"
                    style="background:rgba(71,85,105,0.2); color:#64748b; border:1px solid rgba(71,85,105,0.3);">
                就绪
              </span>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <!-- Device Info -->
          <div class="p-3 rounded-xl space-y-3" style="background:rgba(2,8,23,0.6); border:1px solid rgba(51,65,85,0.4);">
            <!-- 模型标识卡片 -->
            <div class="flex items-center gap-2.5 p-2.5 rounded-lg"
                 :style="`background:${currentModel.iconBg}; border:1px solid ${currentModel.borderColor};`">
              <el-icon size="18" :style="`color:${currentModel.color};`"><component :is="currentModel.icon" /></el-icon>
              <div class="flex-1 min-w-0">
                <div class="font-bold text-sm font-mono leading-tight" :style="`color:${currentModel.color}`">
                  {{ modelType.toUpperCase() }}_v1.0
                </div>
                <div class="text-[10px] text-slate-500 mt-0.5">{{ isDLModel ? '深度学习模型' : '机器学习模型' }}</div>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded flex-shrink-0"
                    :class="isDLModel ? 'text-green-400' : 'text-yellow-400'"
                    style="background:rgba(2,8,23,0.7);">
                {{ isDLModel ? 'GPU' : 'CPU' }}
              </span>
            </div>
            <!-- 2 列紧凑信息 -->
            <div class="grid grid-cols-2 gap-x-3 gap-y-2">
              <div>
                <div class="text-xs text-slate-400 mb-0.5 font-medium">输入 / 输出</div>
                <div class="text-[11px] text-slate-300 font-mono">{{ dsInputDim }} → {{ dsOutputDim }}</div>
              </div>
              <div>
                <div class="text-xs text-slate-400 mb-0.5 font-medium">任务类型</div>
                <div class="text-[11px] text-blue-300 font-mono">回归预测</div>
              </div>
            </div>
          </div>

          <!-- Dataset Config (处理后的训练集) -->
          <div class="p-4 rounded-xl space-y-4 transition-all duration-300"
               :style="`background:${currentModel.iconBg}; border:1px solid ${currentModel.borderColor};`">

            <!-- Header -->
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                     <div class="p-1.5 rounded-lg" :style="`background:${currentModel.activeBg}`">
                         <el-icon size="16" :style="`color:${currentModel.color}`"><Grid /></el-icon>
                     </div>
                     <span class="text-base font-bold tracking-wide" :style="`color:${currentModel.color}`">训练数据集</span>
                </div>
                 <button @click="checkProcessedStatus" class="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg transition hover:bg-white/10"
                         :style="`color:${currentModel.color}; border:1px solid ${currentModel.borderColor}`">
                    <el-icon size="11"><RefreshRight /></el-icon>
                    检查状态
                  </button>
            </div>

            <!-- 数据处理流水线状态 -->
            <div class="space-y-1.5">
              <div class="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-2">数据处理流水线</div>
              <div v-for="(step, idx) in pipelineSteps" :key="step.key"
                   class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg"
                   :style="step.done
                     ? 'background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);'
                     : 'background:rgba(51,65,85,0.1); border:1px solid rgba(51,65,85,0.25);'">
                <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 font-bold"
                      :style="step.done
                        ? 'background:rgba(16,185,129,0.25); color:#34d399;'
                        : 'background:rgba(51,65,85,0.3); color:#64748b;'">
                  {{ step.done ? '✓' : (idx + 1) }}
                </span>
                <span class="text-[11px] flex-1" :class="step.done ? 'text-emerald-300' : 'text-slate-500'">
                  {{ step.label }}
                </span>
                <span v-if="step.done" class="text-[9px] text-slate-600 font-mono flex-shrink-0">完成</span>
                <span v-else class="text-[9px] text-yellow-500/70 font-mono flex-shrink-0">待处理</span>
              </div>
            </div>

            <!-- 训练集就绪：详细信息 -->
            <div v-if="datasetReady"
                 class="p-3 rounded-lg space-y-2.5"
                 style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.2);">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span class="text-emerald-300 text-xs font-bold">训练集已就绪</span>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div class="p-2 rounded-lg text-center bg-black/20 border border-white/5">
                  <div class="text-[10px] text-slate-500 mb-0.5">训练样本</div>
                  <div class="text-xs font-mono font-bold" :style="`color:${currentModel.color}`">
                    {{ processedInfo.trainSamples || '--' }}
                  </div>
                </div>
                <div class="p-2 rounded-lg text-center bg-black/20 border border-white/5">
                  <div class="text-[10px] text-slate-500 mb-0.5">测试样本</div>
                  <div class="text-xs text-emerald-300 font-mono font-bold">
                    {{ processedInfo.testSamples || '--' }}
                  </div>
                </div>
                <div class="p-2 rounded-lg text-center bg-black/20 border border-white/5">
                  <div class="text-[10px] text-slate-500 mb-0.5">输入维度</div>
                  <div class="text-xs text-blue-300 font-mono font-bold">
                    {{ processedInfo.inputDim || '--' }}
                  </div>
                </div>
                <div class="p-2 rounded-lg text-center bg-black/20 border border-white/5">
                  <div class="text-[10px] text-slate-500 mb-0.5">输出维度 (PCA)</div>
                  <div class="text-xs text-purple-300 font-mono font-bold">
                    {{ processedInfo.outputDim || '--' }}
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-1.5 mt-1">
                <span class="text-[10px] text-slate-500">训练/测试比</span>
                <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background:rgba(51,65,85,0.4);">
                  <div class="h-full rounded-full" :style="`width:${(processedInfo.trainRatio || 0.8) * 100}%; background:linear-gradient(90deg,${currentModel.btnGrad});`"></div>
                </div>
                <span class="text-[10px] font-mono font-bold" :style="`color:${currentModel.color}`">
                  {{ ((processedInfo.trainRatio || 0.8) * 100).toFixed(0) }}%
                </span>
              </div>
              <div class="text-[10px] text-slate-600 font-mono mt-1">
                {{ activeDs?.name || '未选择数据集' }} → 模型输入
              </div>
            </div>

            <!-- 训练集未就绪：提示 -->
            <div v-else
                 class="flex items-center gap-2 p-3 rounded-lg"
                 style="background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.2);">
              <el-icon class="text-yellow-500/80 flex-shrink-0" size="14"><Document /></el-icon>
              <span class="text-[11px] text-yellow-400/90 leading-relaxed">
                训练数据尚未就绪，请先前往「数据治理」完成全部处理步骤
                <span class="text-slate-500">（截取 → 划分 → 归一化 → PCA）</span>
              </span>
            </div>
          </div>

          <!-- Start / Stop -->
          <div class="grid grid-cols-2 gap-2">
            <button @click="startTraining" :disabled="training"
                    class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-white transition-all hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed"
                    :style="`background:linear-gradient(135deg,${currentModel.btnGrad}); border:1px solid ${currentModel.borderColor}; box-shadow:0 0 12px ${currentModel.glow};`">
              <el-icon size="13"><VideoPlay /></el-icon>
              {{ training ? '训练中...' : '开始训练' }}
            </button>
            <button @click="stopTraining" :disabled="!training"
                    class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed"
                    style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#f87171;">
              <el-icon size="13"><CircleClose /></el-icon>
              停止训练
            </button>
          </div>

          <!-- Progress -->
          <div class="p-3 rounded-xl space-y-2" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="flex justify-between text-xs">
              <span class="text-slate-400">{{ isDLModel ? 'Epoch 进度' : 'CV Fold 进度' }}</span>
              <span class="font-mono font-bold" :style="`color:${currentModel.color}`">
                {{ currentEpoch }} / {{ totalEpochs }}
              </span>
            </div>
            <div class="h-2 rounded-full overflow-hidden" style="background:rgba(51,65,85,0.5);">
              <div class="h-full rounded-full transition-all duration-300"
                   :style="`width:${progress}%; background:linear-gradient(90deg,${currentModel.btnGrad});`"></div>
            </div>
            <div class="flex justify-between text-[11px] text-slate-600">
              <span>{{ progress }}%</span>
              <span v-if="training && isDLModel">预计剩余 {{ etaStr }}</span>
            </div>
          </div>

          <!-- Realtime Metrics -->
          <div v-if="metrics.trainLoss > 0" class="p-3 rounded-xl space-y-2"
               style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1.5">实时指标</div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">Train Loss</span>
              <span class="text-blue-300 font-mono text-xs">{{ metrics.trainLoss.toFixed(6) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">Test Loss</span>
              <span class="text-emerald-300 font-mono text-xs">{{ metrics.testLoss.toFixed(6) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">最优 Loss</span>
              <span class="text-yellow-300 font-mono text-xs">{{ metrics.bestLoss.toFixed(6) }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Loss Chart -->
      <el-card class="lg:col-span-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(59,130,246,0.15);">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(59,130,246,0.2);">
                <el-icon style="color:#60a5fa;" size="13"><DataAnalysis /></el-icon>
              </div>
              <span class="text-slate-200 font-semibold text-sm">
                {{ isDLModel ? '实时 Loss 收敛曲线' : '交叉验证评分曲线' }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="training" class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full"
                    style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
                实时监控
              </span>
              <button @click="clearChart" class="text-xs px-3 py-1 rounded-lg transition hover:scale-105"
                      style="background:rgba(51,65,85,0.3); color:#64748b; border:1px solid rgba(51,65,85,0.4);">
                清空
              </button>
            </div>
          </div>
        </template>
        <div class="h-[380px] w-full">
          <v-chart class="chart" :option="chartOption" autoresize />
        </div>
      </el-card>
    </div>

    <!-- Console -->
    <el-card style="background:#020817; border:1px solid rgba(51,65,85,0.5);">
      <template #header>
        <div class="flex items-center gap-2">
          <el-icon style="color:#22d3ee;" size="13"><Monitor /></el-icon>
          <span class="font-mono text-xs text-emerald-400">Training Console Output</span>
          <span class="ml-auto text-xs text-slate-600">{{ logs.length }} 条日志</span>
        </div>
      </template>
      <div class="h-44 overflow-y-auto font-mono text-xs space-y-1 custom-scrollbar" id="console">
        <div v-for="(log, idx) in logs" :key="idx">
          <span class="text-slate-600">[{{ log.time }}]</span>
          <span class="ml-2"
                :class="log.type === 'error' ? 'text-red-400' : log.type === 'warn' ? 'text-yellow-400' : 'text-emerald-400/90'">
            {{ log.content }}
          </span>
        </div>
        <div v-if="training" class="text-green-400 animate-pulse">_</div>
        <div v-if="logs.length === 0" class="text-slate-600 italic">等待训练日志输出...</div>
      </div>
    </el-card>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import { VideoPlay, CircleClose, Monitor, DataAnalysis, Refresh,
         Connection, Grid, Timer, Aim, Share, Document, RefreshRight } from '@element-plus/icons-vue';
import DatasetSelector from '../../components/DatasetSelector.vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

// ---- Model type definitions (mirror of ModelArchitecture) ----
const modelTypeDefs = {
  dnn:  { label: 'DNN',  color: '#60a5fa', activeBg: 'rgba(30,58,138,0.22)',  borderColor: 'rgba(59,130,246,0.4)',  glow: 'rgba(59,130,246,0.25)',  iconBgActive: 'rgba(59,130,246,0.25)', iconBg: 'rgba(59,130,246,0.1)',  btnGrad: '#1d4ed8, #3b82f6', icon: Connection },
  cnn:  { label: 'CNN',  color: '#818cf8', activeBg: 'rgba(49,46,129,0.22)',  borderColor: 'rgba(99,102,241,0.4)',  glow: 'rgba(99,102,241,0.25)',  iconBgActive: 'rgba(99,102,241,0.25)', iconBg: 'rgba(99,102,241,0.1)',  btnGrad: '#4338ca, #6366f1', icon: Grid },
  lstm: { label: 'LSTM', color: '#c084fc', activeBg: 'rgba(88,28,135,0.22)',  borderColor: 'rgba(168,85,247,0.4)', glow: 'rgba(168,85,247,0.25)', iconBgActive: 'rgba(168,85,247,0.25)', iconBg: 'rgba(168,85,247,0.1)', btnGrad: '#7c3aed, #a855f7', icon: Timer },
  svm:  { label: 'SVM',  color: '#34d399', activeBg: 'rgba(6,78,59,0.22)',    borderColor: 'rgba(16,185,129,0.4)', glow: 'rgba(16,185,129,0.25)', iconBgActive: 'rgba(16,185,129,0.25)', iconBg: 'rgba(16,185,129,0.1)', btnGrad: '#065f46, #10b981', icon: Aim },
  rf:   { label: 'RF',   color: '#fbbf24', activeBg: 'rgba(120,53,15,0.22)',  borderColor: 'rgba(245,158,11,0.4)', glow: 'rgba(245,158,11,0.25)', iconBgActive: 'rgba(245,158,11,0.25)', iconBg: 'rgba(245,158,11,0.1)', btnGrad: '#92400e, #f59e0b', icon: Share },
};

// ---- Config state ----
const savedConfig = ref({});
const modelType = ref('dnn');
const totalEpochs = ref(3000);

// ---- Dataset state ----
const dsSelectorRef = ref(null);
const activeDs = ref(null);
const dsInputDim = computed(() => activeDs.value?.trainInfo?.inputDim || activeDs.value?.inputVariables?.length || '?');
const dsOutputDim = computed(() => {
  const ds = activeDs.value;
  if (ds?.trainInfo?.outputDim) return ds.trainInfo.outputDim;
  if (ds?.processConfig?.pcaComponents) return ds.processConfig.pcaComponents;
  return ds?.outputVariable?.spatialPoints || '?';
});

function onDatasetChange(ds) {
  activeDs.value = ds;
  checkProcessedStatus();
}


const reloadConfig = () => {
  try {
    const raw = localStorage.getItem('model_config');
    savedConfig.value = raw ? JSON.parse(raw) : {};
    modelType.value = savedConfig.value.modelType || 'dnn';
    totalEpochs.value = savedConfig.value.dlParams?.epochs || 3000;
    addLog(`配置同步完成：当前模型 → ${modelType.value.toUpperCase()}`, 'info');
  } catch {
    addLog('读取配置失败，使用默认 DNN 参数', 'warn');
  }
};

onMounted(() => {
  reloadConfig();
  checkProcessedStatus();
});

const currentModel = computed(() => modelTypeDefs[modelType.value] || modelTypeDefs.dnn);
const isDLModel = computed(() => ['dnn', 'cnn', 'lstm'].includes(modelType.value));

const dnnLayerStr = computed(() => {
  const layers = savedConfig.value.dnn?.hiddenLayers;
  const inD = savedConfig.value.inputDim || dsInputDim.value || '?';
  const outD = savedConfig.value.outputDim || dsOutputDim.value || '?';
  if (!layers?.length) return `${inD}→…→${outD}`;
  return `${inD}→${layers.map(l => l.units).join('→')}→${outD}`;
});

// ---- Training state ----
const training = ref(false);
const currentEpoch = ref(0);
const lossData = ref([]);
const testLossData = ref([]);
const epochLabels = ref([]);
const metrics = reactive({ trainLoss: 0, testLoss: 0, bestLoss: Infinity });

const progress = computed(() => Math.min(100, Math.round((currentEpoch.value / totalEpochs.value) * 100)));
const etaStr = computed(() => {
  if (!training.value || currentEpoch.value === 0) return '--';
  const remaining = totalEpochs.value - currentEpoch.value;
  const secs = Math.round((remaining / 30) * 0.5);
  return secs < 60 ? `${secs}s` : `${Math.round(secs / 60)}min`;
});

const logs = ref([
  { time: '--:--:--', content: 'SYSTEM: 训练引擎就绪，等待指令...', type: 'info' }
]);
const addLog = (content, type = 'info') =>
  logs.value.push({ time: new Date().toLocaleTimeString(), content, type });

// ---- Dataset state (processed pipeline) ----
const pipelineSteps = ref([
  { key: 'cut',    label: '① 稳态截取 · Cut',         done: false },
  { key: 'split',  label: '② 训练/测试划分 · Split',   done: false },
  { key: 'zscore', label: '③ Z-Score 归一化',          done: false },
  { key: 'pca',    label: '④ PCA 降维',                done: false },
]);
const datasetReady = ref(false);
const processedInfo = reactive({
  trainSamples: 0,
  testSamples: 0,
  inputDim: 0,
  outputDim: 0,
  rawOutputDim: 0,
  trainRatio: 0,
});

const checkProcessedStatus = async () => {
  // 优先使用数据集 API
  if (activeDs.value) {
    try {
      const resp = await fetch(`http://127.0.0.1:5000/api/dataset/${activeDs.value.id}/status`);
      const data = await resp.json();
      if (data.pipeline) {
        pipelineSteps.value.forEach(s => {
          if (data.pipeline[s.key]) s.done = data.pipeline[s.key].done;
        });
      }
      datasetReady.value = !!data.ready;
      if (data.trainInfo) {
        Object.assign(processedInfo, data.trainInfo);
      }
      if (data.ready) {
        addLog(`训练数据就绪 [${activeDs.value.name}]：${data.trainInfo?.trainSamples} 训练 / ${data.trainInfo?.testSamples} 测试`, 'info');
      } else {
        addLog(`数据集 [${activeDs.value.name}] 尚未完成全部处理步骤`, 'warn');
      }
      return;
    } catch { /* fall through to legacy */ }
  }

  // Legacy fallback
  try {
    const resp = await fetch('http://127.0.0.1:5000/api/data/processed-status');
    const data = await resp.json();
    // 更新流水线状态
    if (data.pipeline) {
      pipelineSteps.value.forEach(s => {
        if (data.pipeline[s.key]) s.done = data.pipeline[s.key].done;
      });
    }
    datasetReady.value = !!data.ready;
    if (data.trainInfo) {
      Object.assign(processedInfo, data.trainInfo);
    }
    if (data.ready) {
      addLog(`训练数据就绪：${data.trainInfo?.trainSamples} 训练 / ${data.trainInfo?.testSamples} 测试`, 'info');
    } else {
      addLog('训练数据尚未就绪，请先完成数据治理流程', 'warn');
    }
  } catch {
    // 后端不可用时 fallback：读取 localStorage 中的流水线状态
    try {
      const local = JSON.parse(localStorage.getItem('pipeline_status') || '{}');
      pipelineSteps.value.forEach(s => {
        if (local[s.key]) s.done = !!local[s.key].done;
      });
      datasetReady.value = pipelineSteps.value.every(s => s.done);
    } catch { /* ignore */ }
    addLog('无法连接后端，已使用本地缓存状态', 'warn');
  }
};

// ---- ECharts ----
const chartOption = ref({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(2,8,23,0.95)',
    borderColor: 'rgba(51,65,85,0.6)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
  },
  legend: { textStyle: { color: '#94a3b8' }, data: ['Train Loss', 'Test Loss'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category', boundaryGap: false,
    axisLabel: { color: '#64748b', fontSize: 11 },
    axisLine: { lineStyle: { color: '#1e293b' } },
    data: [],
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: '#1e293b' } },
  },
  series: [
    {
      name: 'Train Loss', type: 'line', smooth: true, showSymbol: false, data: [],
      lineStyle: { color: '#3b82f6', width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.25)' }, { offset: 1, color: 'rgba(59,130,246,0)' }] } },
    },
    {
      name: 'Test Loss', type: 'line', smooth: true, showSymbol: false, data: [],
      lineStyle: { color: '#10b981', width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(16,185,129,0.18)' }, { offset: 1, color: 'rgba(16,185,129,0)' }] } },
    },
  ],
});

const clearChart = () => {
  lossData.value = []; testLossData.value = []; epochLabels.value = [];
  chartOption.value.xAxis.data = [];
  chartOption.value.series[0].data = [];
  chartOption.value.series[1].data = [];
  currentEpoch.value = 0;
  Object.assign(metrics, { trainLoss: 0, testLoss: 0, bestLoss: Infinity });
};

// ---- Training simulation ----
let trainingInterval = null;

const startTraining = () => {
  if (training.value) return;
  if (!datasetReady.value) {
    addLog('⚠ 训练数据未就绪！请先前往「数据治理」完成全部处理步骤', 'warn');
    return;
  }
  training.value = true;
  clearChart();
  addLog(`数据集：${activeDs.value?.name || '默认'} — 输入(${processedInfo.trainSamples}×${processedInfo.inputDim}) + 输出(${processedInfo.trainSamples}×${processedInfo.outputDim})`, 'info');
  addLog(`启动 ${modelType.value.toUpperCase()} 训练 | ${isDLModel.value ? `共 ${totalEpochs.value} Epoch` : `${savedConfig.value.mlParams?.cvFolds || 5}-Fold CV`}`, 'info');

  trainingInterval = setInterval(() => {
    if (currentEpoch.value >= totalEpochs.value) {
      clearInterval(trainingInterval);
      training.value = false;
      addLog(`✓ 训练完成！最优 Loss: ${metrics.bestLoss.toFixed(8)}`, 'info');
      return;
    }
    currentEpoch.value += 30;
    const l  = Math.exp(-currentEpoch.value / 600) * 0.12 + Math.random() * 0.0008;
    const tl = l * (1.05 + Math.random() * 0.08);

    lossData.value.push(+l.toFixed(8));
    testLossData.value.push(+tl.toFixed(8));
    epochLabels.value.push(currentEpoch.value);
    Object.assign(metrics, { trainLoss: l, testLoss: tl, bestLoss: Math.min(metrics.bestLoss, l) });

    chartOption.value.xAxis.data = [...epochLabels.value];
    chartOption.value.series[0].data = [...lossData.value];
    chartOption.value.series[1].data = [...testLossData.value];

    if (currentEpoch.value % 300 === 0) {
      addLog(`Epoch ${currentEpoch.value} | TrainLoss: ${l.toFixed(8)} | TestLoss: ${tl.toFixed(8)}`, 'info');
      const el = document.getElementById('console');
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, 500);
};

const stopTraining = () => {
  if (trainingInterval) clearInterval(trainingInterval);
  training.value = false;
  addLog('训练任务已被用户中止。', 'error');
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }


.config-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  color: #94a3b8;
  background: rgba(2, 8, 23, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.5);
  white-space: nowrap;
}
.config-chip span {
  color: #e2e8f0;
  font-weight: 600;
  font-family: monospace;
}
</style>
