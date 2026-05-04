<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#1d4ed8,#4f46e5); box-shadow:0 0 20px rgba(59,130,246,0.4);">
            <el-icon size="20" style="color:white;"><Operation /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#60a5fa,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            模型架构设计
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">深度学习 / 机器学习模型拓扑结构与超参数配置</p>
      </div>
      <button @click="saveConfig"
              class="btn-glow flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
              style="background:linear-gradient(135deg,#2563eb,#4f46e5); border:1px solid rgba(99,102,241,0.4);">
        <el-icon><Checked /></el-icon>
        保存全局配置
      </button>
    </div>

    <!-- Dataset Selector Bar -->
    <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <DatasetSelector ref="dsSelectorRef" @change="onDatasetChange" />
      <div v-if="activeDataset" class="flex items-center gap-3 mt-2">
        <span class="text-slate-500 text-[11px]">模型输入/输出维度将从数据集自动获取：</span>
        <span class="text-blue-300 font-mono text-xs font-bold">{{ activeInputDim }}D → {{ activeOutputDim }}D</span>
        <span v-if="activeRawOutputDim && activeRawOutputDim !== activeOutputDim" class="text-slate-500 text-[11px]">
          (原始 {{ activeRawOutputDim }} 维，PCA 压缩至 {{ activeOutputDim }} 维)
        </span>
      </div>
    </div>

    <!-- Model Type Selector -->
    <div class="grid grid-cols-4 gap-3">
      <div v-for="m in modelTypes" :key="m.id"
           @click="selectedModel = m.id"
           class="cursor-pointer rounded-xl p-4 transition-all duration-200 hover:scale-[1.02]"
           :style="selectedModel === m.id
             ? `background:${m.activeBg}; border:1.5px solid ${m.borderColor}; box-shadow:0 0 18px ${m.glow};`
             : 'background:rgba(10,18,36,0.7); border:1px solid rgba(51,65,85,0.4);'">
        <div class="flex flex-col gap-2.5">
          <div class="w-9 h-9 rounded-lg flex items-center justify-center"
               :style="`background:${selectedModel === m.id ? m.iconBgActive : m.iconBg};`">
            <el-icon size="18" :style="`color:${m.color};`"><component :is="m.icon" /></el-icon>
          </div>
          <div>
            <div class="font-bold text-sm tracking-wide"
                 :style="`color:${selectedModel === m.id ? m.color : '#94a3b8'}`">{{ m.label }}</div>
            <div class="text-[11px] text-slate-500 mt-0.5 leading-tight">{{ m.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Config Grid -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-5">

      <!-- ===== DNN ===== -->
      <template v-if="selectedModel === 'dnn'">
        <el-card class="xl:col-span-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(59,130,246,0.15);">
          <template #header>
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-2">
                <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(59,130,246,0.2);">
                  <el-icon style="color:#60a5fa;" size="13"><Connection /></el-icon>
                </div>
                <span class="text-slate-200 font-semibold text-sm">DNN 全连接层拓扑设计</span>
                <span class="text-xs px-2 py-0.5 rounded-full ml-1"
                      style="background:rgba(59,130,246,0.12); color:#93c5fd; border:1px solid rgba(59,130,246,0.2);">
                  {{ dnnConfig.hiddenLayers.length + 2 }} 层
                </span>
              </div>
              <button @click="addDnnLayer"
                      class="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all hover:scale-105"
                      style="background:rgba(59,130,246,0.12); color:#60a5fa; border:1px solid rgba(59,130,246,0.25);">
                <el-icon size="13"><CirclePlus /></el-icon> 添加隐藏层
              </button>
            </div>
          </template>
          <div class="space-y-3">
            <div class="layer-row" style="background:rgba(30,58,138,0.12); border-color:rgba(59,130,246,0.25);">
              <div class="indicator-blue"></div>
              <div class="flex-1">
                <div class="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-0.5">Input Layer</div>
                <div class="text-slate-400 font-semibold text-sm">输入特征层</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-slate-400 text-xs">维度:</span>
                <span class="text-blue-300 font-bold font-mono text-lg">{{ activeInputDim }}</span>
              </div>
              <div class="text-right">
                <div class="text-slate-400 text-xs">{{ inputDimDesc }}</div>
                <div class="text-slate-500 text-[11px]">由数据集定义</div>
              </div>
            </div>
            <TransitionGroup name="layer-list">
              <div v-for="(layer, index) in dnnConfig.hiddenLayers" :key="layer.id" class="layer-row group">
                <div class="indicator-gray"></div>
                <div style="min-width:90px;">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-0.5">Hidden {{ index + 1 }}</div>
                  <div class="text-slate-400 font-medium text-sm">全连接层</div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-xs">神经元:</span>
                  <el-input-number v-model="layer.units" :min="1" :max="2048" size="small" controls-position="right" style="width:110px;" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-xs">激活:</span>
                  <el-select v-model="layer.activation" size="small" style="width:120px;">
                    <el-option label="ReLU" value="relu" />
                    <el-option label="Sigmoid" value="sigmoid" />
                    <el-option label="Tanh" value="tanh" />
                    <el-option label="LeakyReLU" value="leaky_relu" />
                  </el-select>
                </div>
                <button @click="removeDnnLayer(index)"
                        class="ml-auto opacity-0 group-hover:opacity-100 transition-all w-7 h-7 rounded-lg flex items-center justify-center"
                        style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#f87171;">
                  <el-icon size="13"><Delete /></el-icon>
                </button>
              </div>
            </TransitionGroup>
            <div class="layer-row" style="background:rgba(6,78,59,0.12); border-color:rgba(16,185,129,0.25);">
              <div class="indicator-green"></div>
              <div class="flex-1">
                <div class="text-[10px] font-bold uppercase tracking-widest text-green-400 mb-0.5">Output Layer</div>
                <div class="text-slate-400 font-semibold text-sm">场点预测层</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-slate-400 text-xs">维度:</span>
                <span class="text-green-300 font-bold font-mono text-lg">{{ activeOutputDim }}</span>
              </div>
              <div class="text-right">
                <div class="text-slate-400 text-xs">{{ outputDimDesc }}</div>
                <div class="text-slate-500 text-[11px]">{{ outputUnitDesc }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </template>

      <!-- ===== CNN ===== -->
      <template v-if="selectedModel === 'cnn'">
        <el-card class="xl:col-span-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <template #header>
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-2">
                <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(99,102,241,0.2);">
                  <el-icon style="color:#818cf8;" size="13"><Grid /></el-icon>
                </div>
                <span class="text-slate-200 font-semibold text-sm">CNN-1D 卷积特征提取层</span>
                <span class="text-xs px-2 py-0.5 rounded-full ml-1"
                      style="background:rgba(99,102,241,0.12); color:#a5b4fc; border:1px solid rgba(99,102,241,0.2);">
                  {{ cnnConfig.convLayers.length }} 个卷积块
                </span>
              </div>
              <button @click="addCnnLayer"
                      class="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all hover:scale-105"
                      style="background:rgba(99,102,241,0.12); color:#818cf8; border:1px solid rgba(99,102,241,0.25);">
                <el-icon size="13"><CirclePlus /></el-icon> 添加卷积块
              </button>
            </div>
          </template>
          <div class="space-y-3">
            <TransitionGroup name="layer-list">
              <div v-for="(layer, index) in cnnConfig.convLayers" :key="layer.id" class="layer-row group">
                <div class="indicator-indigo"></div>
                <div style="min-width:90px;">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-0.5">Conv1D {{ index + 1 }}</div>
                  <div class="text-slate-400 font-medium text-sm">卷积块</div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-xs">滤波器:</span>
                  <el-input-number v-model="layer.filters" :min="1" :max="512" size="small" controls-position="right" style="width:95px;" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-xs">核大小:</span>
                  <el-input-number v-model="layer.kernelSize" :min="1" :max="32" size="small" controls-position="right" style="width:85px;" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-xs">激活:</span>
                  <el-select v-model="layer.activation" size="small" style="width:95px;">
                    <el-option label="ReLU" value="relu" />
                    <el-option label="Tanh" value="tanh" />
                    <el-option label="GELU" value="gelu" />
                  </el-select>
                </div>
                <div class="flex items-center gap-1.5">
                  <el-checkbox v-model="layer.pooling" size="small">
                    <span class="text-slate-500 text-xs">Pooling</span>
                  </el-checkbox>
                </div>
                <button @click="removeCnnLayer(index)"
                        class="ml-auto opacity-0 group-hover:opacity-100 transition-all w-7 h-7 rounded-lg flex items-center justify-center"
                        style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#f87171;">
                  <el-icon size="13"><Delete /></el-icon>
                </button>
              </div>
            </TransitionGroup>
            <!-- Flatten + Dense Head -->
            <div class="layer-row" style="background:rgba(49,46,129,0.1); border-color:rgba(99,102,241,0.2);">
              <div class="indicator-indigo"></div>
              <div class="flex-1">
                <div class="text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-0.5">Flatten + Dense Head</div>
                <div class="text-slate-400 text-sm">展平层 → 全连接输出</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-slate-500 text-xs">FC 节点:</span>
                <el-input-number v-model="cnnConfig.fcUnits" :min="1" :max="2048" size="small" controls-position="right" style="width:110px;" />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-slate-400 text-xs">输出:</span>
                <span class="text-indigo-300 font-mono font-bold">{{ cnnConfig.outputDim }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </template>

      <!-- ===== RF ===== -->
      <template v-if="selectedModel === 'rf'">
        <el-card class="xl:col-span-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(245,158,11,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(245,158,11,0.2);">
                <el-icon style="color:#fbbf24;" size="13"><Share /></el-icon>
              </div>
              <span class="text-slate-200 font-semibold text-sm">随机森林集成超参数</span>
            </div>
          </template>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="text-xs text-slate-400 mb-1.5 font-medium">决策树数量 (n_estimators)</div>
              <el-input-number v-model="rfConfig.nEstimators" :min="10" :max="2000" :step="10" class="w-full" controls-position="right" />
              <div class="text-[10px] text-slate-600 mt-1">越多越稳定，计算量也越大</div>
            </div>
            <div>
              <div class="text-xs text-slate-400 mb-1.5 font-medium">最大树深 (max_depth)</div>
              <el-input-number v-model="rfConfig.maxDepth" :min="1" :max="100" class="w-full" controls-position="right" />
              <div class="text-[10px] text-slate-600 mt-1">限制过拟合，None 为不限制</div>
            </div>
            <div>
              <div class="text-xs text-slate-400 mb-1.5 font-medium">最小分裂样本数 (min_samples_split)</div>
              <el-input-number v-model="rfConfig.minSamplesSplit" :min="2" :max="100" class="w-full" controls-position="right" />
            </div>
            <div>
              <div class="text-xs text-slate-400 mb-1.5 font-medium">最小叶节点样本 (min_samples_leaf)</div>
              <el-input-number v-model="rfConfig.minSamplesLeaf" :min="1" :max="100" class="w-full" controls-position="right" />
            </div>
            <div>
              <div class="text-xs text-slate-400 mb-1.5 font-medium">特征采样策略 (max_features)</div>
              <el-select v-model="rfConfig.maxFeatures" class="w-full">
                <el-option label="sqrt (推荐)" value="sqrt" />
                <el-option label="log2" value="log2" />
                <el-option label="全部特征" value="1.0" />
              </el-select>
            </div>
            <div class="flex flex-col gap-3 pt-1">
              <div class="text-xs text-slate-400 font-medium">启用选项</div>
              <div class="flex items-center gap-2">
                <el-switch v-model="rfConfig.bootstrap" style="--el-switch-on-color:#f59e0b;" />
                <span class="text-slate-400 text-xs">Bootstrap 重采样</span>
              </div>
              <div class="flex items-center gap-2">
                <el-switch v-model="rfConfig.oobScore" style="--el-switch-on-color:#f59e0b;" />
                <span class="text-slate-400 text-xs">OOB 袋外误差评估</span>
              </div>
            </div>
          </div>
        </el-card>
      </template>

      <!-- ===== Right Panel ===== -->
      <div class="space-y-4">
        <!-- DL: Training Hyperparams -->
        <el-card v-if="isDLModel" style="background:rgba(10,18,36,0.85); border:1px solid rgba(59,130,246,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(139,92,246,0.2);">
                <el-icon style="color:#a78bfa;" size="13"><Setting /></el-icon>
              </div>
              <span class="text-slate-200 font-semibold text-sm">训练超参数</span>
            </div>
          </template>
          <el-form :model="dlParams" label-position="top" size="small">
            <el-form-item>
              <template #label><span class="text-slate-400 text-xs">优化器算法</span></template>
              <el-select v-model="dlParams.optimizer" class="w-full">
                <el-option label="Adam (自适应矩估计)" value="Adam" />
                <el-option label="SGD (随机梯度下降)" value="SGD" />
                <el-option label="RMSprop" value="RMSprop" />
                <el-option label="AdamW (权重衰减)" value="AdamW" />
              </el-select>
            </el-form-item>
            <div class="grid grid-cols-2 gap-3">
              <el-form-item>
                <template #label><span class="text-slate-400 text-xs">初始学习率</span></template>
                <el-input v-model="dlParams.lr" placeholder="1e-4" />
              </el-form-item>
              <el-form-item>
                <template #label><span class="text-slate-400 text-xs">批次大小</span></template>
                <el-input-number v-model="dlParams.batchSize" :min="1" class="w-full" controls-position="right" />
              </el-form-item>
            </div>
            <el-form-item>
              <template #label>
                <div class="flex justify-between w-full">
                  <span class="text-slate-400 text-xs">训练轮数 (Epochs)</span>
                  <span class="text-blue-400 font-mono text-xs font-bold">{{ dlParams.epochs }}</span>
                </div>
              </template>
              <el-slider v-model="dlParams.epochs" :min="100" :max="10000" :step="100"
                         style="--el-slider-main-bg-color:#3b82f6;" />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- ML: Cross-Validation Config -->
        <el-card v-if="!isDLModel" style="background:rgba(10,18,36,0.85); border:1px solid rgba(16,185,129,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(16,185,129,0.2);">
                <el-icon style="color:#34d399;" size="13"><Setting /></el-icon>
              </div>
              <span class="text-slate-200 font-semibold text-sm">交叉验证配置</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item>
              <template #label><span class="text-slate-400 text-xs">评估指标</span></template>
              <el-select v-model="mlParams.scoring" class="w-full">
                <el-option label="MAE (平均绝对误差)" value="neg_mean_absolute_error" />
                <el-option label="MSE (均方误差)" value="neg_mean_squared_error" />
                <el-option label="R² Score" value="r2" />
                <el-option label="MAPE (相对误差%)" value="neg_mean_absolute_percentage_error" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <template #label>
                <div class="flex justify-between w-full">
                  <span class="text-slate-400 text-xs">K 折交叉验证</span>
                  <span class="text-emerald-400 font-mono text-xs font-bold">{{ mlParams.cvFolds }}-Fold</span>
                </div>
              </template>
              <el-slider v-model="mlParams.cvFolds" :min="3" :max="10" :step="1"
                         style="--el-slider-main-bg-color:#10b981;" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="text-slate-400 text-xs">并行核心数 (n_jobs)</span></template>
              <el-input-number v-model="mlParams.nJobs" :min="-1" :max="32" class="w-full" controls-position="right" />
              <div class="text-[10px] text-slate-600 mt-1">-1 表示使用全部 CPU 核心</div>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Model Summary -->
        <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(139,92,246,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded flex items-center justify-center" style="background:rgba(245,158,11,0.2);">
                <el-icon style="color:#fbbf24;" size="13"><Monitor /></el-icon>
              </div>
              <span class="text-slate-200 font-semibold text-sm">模型信息摘要</span>
            </div>
          </template>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">当前模型</span>
              <span class="font-bold text-xs px-2.5 py-0.5 rounded-full"
                    :style="`background:${currentModelInfo.iconBg}; color:${currentModelInfo.color}; border:1px solid ${currentModelInfo.borderColor};`">
                {{ currentModelInfo.label }}
              </span>
            </div>
            <div v-if="isDLModel" class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">预估参数量</span>
              <span class="text-slate-200 font-mono text-xs font-semibold">~{{ estimatedParams }}</span>
            </div>
            <div v-if="!isDLModel" class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">算法类型</span>
              <span class="text-slate-300 text-xs">集成学习 (Bagging)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">任务类型</span>
              <span class="text-blue-300 text-xs font-mono">回归预测</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">损失函数</span>
              <span class="text-blue-300 text-xs font-mono">{{ isDLModel ? 'MAE (L1Loss)' : 'MSE / MAE' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-slate-500 text-xs">运行设备</span>
              <span class="text-xs font-semibold" :style="`color:${isDLModel ? '#4ade80' : '#fbbf24'};`">
                {{ isDLModel ? 'CUDA / GPU' : 'CPU multi-core' }}
              </span>
            </div>
          </div>
        </el-card>
      </div>

    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Checked, CirclePlus, Delete, Connection, Setting, Monitor,
  Grid, Share, Operation
} from '@element-plus/icons-vue';
import DatasetSelector from '../../components/DatasetSelector.vue';

// ---- Dataset state ----
const dsSelectorRef = ref(null);
const activeDataset = ref(null);

const activeInputDim = computed(() => {
  const ds = activeDataset.value;
  if (ds?.trainInfo?.inputDim) return ds.trainInfo.inputDim;
  return ds?.inputVariables?.length || 4;
});

const activeOutputDim = computed(() => {
  const ds = activeDataset.value;
  if (ds?.trainInfo?.outputDim) return ds.trainInfo.outputDim;
  if (ds?.processConfig?.pcaComponents) return ds.processConfig.pcaComponents;
  return ds?.outputVariable?.spatialPoints || 1241;
});

const activeRawOutputDim = computed(() => {
  const ds = activeDataset.value;
  return ds?.trainInfo?.rawOutputDim || ds?.outputVariable?.spatialPoints || null;
});

const inputDimDesc = computed(() => {
  const vars = activeDataset.value?.inputVariables || [];
  if (vars.length === 0) return '输入特征';
  return vars.map(v => `${v.name}(${v.unit})`).join(', ');
});

const outputDimDesc = computed(() => {
  const raw = activeRawOutputDim.value;
  const pca = activeOutputDim.value;
  if (raw && raw !== pca) return `${raw} 场点 → PCA ${pca} 维`;
  return `${pca} 个场点`;
});

const outputUnitDesc = computed(() => {
  const ds = activeDataset.value;
  const name = ds?.outputVariable?.name || '电磁场';
  const unit = ds?.outputVariable?.unit || '';
  return unit ? `${name}分布 (${unit})` : `${name}分布`;
});

function onDatasetChange(ds) {
  activeDataset.value = ds;
  // 自动同步维度到各模型配置
  dnnConfig.inputDim = activeInputDim.value;
  dnnConfig.outputDim = activeOutputDim.value;
  cnnConfig.outputDim = activeOutputDim.value;
}

const selectedModel = ref('dnn');

const modelTypes = [
  {
    id: 'dnn', label: 'DNN', desc: '全连接深度网络',
    color: '#60a5fa', activeBg: 'rgba(30,58,138,0.3)',
    borderColor: 'rgba(59,130,246,0.5)', glow: 'rgba(59,130,246,0.2)',
    iconBg: 'rgba(59,130,246,0.1)', iconBgActive: 'rgba(59,130,246,0.25)', icon: Connection,
  },
  {
    id: 'cnn', label: 'CNN', desc: '卷积神经网络',
    color: '#818cf8', activeBg: 'rgba(49,46,129,0.3)',
    borderColor: 'rgba(99,102,241,0.5)', glow: 'rgba(99,102,241,0.2)',
    iconBg: 'rgba(99,102,241,0.1)', iconBgActive: 'rgba(99,102,241,0.25)', icon: Grid,
  },
  {
    id: 'rf', label: 'RF', desc: '随机森林集成',
    color: '#fbbf24', activeBg: 'rgba(120,53,15,0.3)',
    borderColor: 'rgba(245,158,11,0.5)', glow: 'rgba(245,158,11,0.2)',
    iconBg: 'rgba(245,158,11,0.1)', iconBgActive: 'rgba(245,158,11,0.25)', icon: Share,
  },
];

// ---- DNN ----
const dnnConfig = reactive({
  inputDim: 4, outputDim: 1241,
  hiddenLayers: [
    { id: 1, units: 16, activation: 'relu' },
    { id: 2, units: 32, activation: 'relu' },
    { id: 3, units: 64, activation: 'relu' },
  ],
});
const addDnnLayer = () => {
  const newId = dnnConfig.hiddenLayers.length > 0 ? Math.max(...dnnConfig.hiddenLayers.map(l => l.id)) + 1 : 1;
  dnnConfig.hiddenLayers.push({ id: newId, units: 128, activation: 'relu' });
};
const removeDnnLayer = (i) => dnnConfig.hiddenLayers.splice(i, 1);

// ---- CNN ----
const cnnConfig = reactive({
  outputDim: 1241, fcUnits: 256,
  convLayers: [
    { id: 1, filters: 32, kernelSize: 3, activation: 'relu', pooling: true },
    { id: 2, filters: 64, kernelSize: 3, activation: 'relu', pooling: false },
  ],
});
const addCnnLayer = () => {
  const newId = cnnConfig.convLayers.length > 0 ? Math.max(...cnnConfig.convLayers.map(l => l.id)) + 1 : 1;
  cnnConfig.convLayers.push({ id: newId, filters: 128, kernelSize: 3, activation: 'relu', pooling: false });
};
const removeCnnLayer = (i) => cnnConfig.convLayers.splice(i, 1);


// ---- RF ----
const rfConfig = reactive({
  nEstimators: 100, maxDepth: 20, minSamplesSplit: 2, minSamplesLeaf: 1,
  maxFeatures: 'sqrt', bootstrap: true, oobScore: false,
});

// ---- Shared DL params ----
const dlParams = reactive({ optimizer: 'Adam', lr: '0.0001', batchSize: 16, epochs: 3000 });

// ---- Shared ML params ----
const mlParams = reactive({ scoring: 'neg_mean_absolute_error', cvFolds: 5, nJobs: -1 });

// ---- Computed ----
const isDLModel = computed(() => ['dnn', 'cnn'].includes(selectedModel.value));
const currentModelInfo = computed(() => modelTypes.find(m => m.id === selectedModel.value) || modelTypes[0]);
const estimatedParams = computed(() => {
  if (selectedModel.value !== 'dnn') return 'N/A';
  const layers = [activeInputDim.value, ...dnnConfig.hiddenLayers.map(l => l.units), activeOutputDim.value];
  let total = 0;
  for (let i = 0; i < layers.length - 1; i++) total += layers[i] * layers[i + 1] + layers[i + 1];
  return total > 1e6 ? (total / 1e6).toFixed(1) + 'M' : (total / 1e3).toFixed(1) + 'K';
});

const saveConfig = () => {
  const config = {
    modelType: selectedModel.value,
    datasetId: activeDataset.value?.id || null,
    inputDim: activeInputDim.value,
    outputDim: activeOutputDim.value,
    rawOutputDim: activeRawOutputDim.value,
    dnn: dnnConfig, cnn: cnnConfig, rf: rfConfig,
    dlParams, mlParams,
  };
  localStorage.setItem('model_config', JSON.stringify(config));
  ElMessage({ message: `${selectedModel.value.toUpperCase()} 配置已同步至训练引擎`, type: 'success', duration: 2000 });
};
</script>

<style scoped>
.layer-list-enter-active, .layer-list-leave-active { transition: all 0.35s cubic-bezier(0.4,0,0.2,1); }
.layer-list-enter-from, .layer-list-leave-to { opacity: 0; transform: translateX(-16px); }
.indicator-indigo { width: 4px; flex-shrink: 0; border-radius: 2px; background: #6366f1; }
</style>
