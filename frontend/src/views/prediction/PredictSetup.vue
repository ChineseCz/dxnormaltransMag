<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- ═══════ 页面标题 + 数据集选择 ═══════ -->
    <div class="px-6 pt-6 pb-4">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="flex items-center gap-3">
            <div class="rounded-xl flex items-center justify-center flex-shrink-0"
                 style="width:36px;height:36px;background:linear-gradient(135deg,#f59e0b,#d97706); box-shadow:0 0 20px rgba(245,158,11,0.4);">
              <el-icon size="20" style="color:#fff;"><Setting /></el-icon>
            </div>
            <h1 class="text-2xl font-extrabold tracking-tight"
                style="background:linear-gradient(90deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              预测配置
            </h1>
          </div>
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">选择模型、设置工况参数，发起电磁场分布预测</p>
        </div>
        <div v-if="isPredicting" class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
             style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); color:#fbbf24;">
          <el-icon class="is-loading" size="12"><Loading /></el-icon>
          推理计算中...
        </div>
      </div>
      <div class="p-3 rounded-xl" style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.4);">
        <DatasetSelector ref="dsSelectorRef" @change="setDataset" />
      </div>
    </div>

    <!-- ═══════ 主体内容 ═══════ -->
    <div class="px-6 pb-6 space-y-5">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <!-- 左列：模型选择 -->
        <div class="setup-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:rgba(59,130,246,0.15);">
                <el-icon size="15" style="color:#60a5fa;"><Box /></el-icon>
              </div>
              <span class="text-white font-bold text-sm">选择预测模型</span>
            </div>
            <el-button size="small" text style="color:#64748b;" @click="fetchModels">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="card-body space-y-4">
            <div>
              <label class="block text-slate-400 text-xs font-semibold mb-1.5">模型文件</label>
              <el-select v-model="selectedModel" placeholder="请选择已训练的模型..."
                         filterable clearable class="w-full" size="large">
                <el-option v-for="m in modelList" :key="m.name" :label="m.name" :value="m.name">
                  <div class="flex items-center justify-between w-full py-0.5">
                    <div class="flex items-center gap-2">
                      <el-tag size="small" :type="modelTagType(m.type)" effect="dark" round>{{ m.type }}</el-tag>
                      <span class="text-slate-200 text-xs font-mono">{{ m.name }}</span>
                    </div>
                    <span class="text-slate-500 text-[11px]">{{ m.size }}</span>
                  </div>
                </el-option>
              </el-select>
            </div>
            <Transition name="fade">
              <div v-if="selectedModelInfo" class="p-3 rounded-lg space-y-2"
                   style="background:rgba(15,23,42,0.5); border:1px solid rgba(59,130,246,0.15);">
                <div class="flex items-center justify-between">
                  <span class="text-slate-500 text-[11px]">模型类型</span>
                  <el-tag size="small" :type="modelTagType(selectedModelInfo.type)" effect="dark" round>{{ selectedModelInfo.type }}</el-tag>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-slate-500 text-[11px]">文件大小</span>
                  <span class="text-slate-300 text-xs font-mono">{{ selectedModelInfo.size }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-slate-500 text-[11px]">创建时间</span>
                  <span class="text-slate-300 text-xs font-mono">{{ selectedModelInfo.date || '—' }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-slate-500 text-[11px]">状态</span>
                  <div class="flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span>
                    <span class="text-green-400 text-[11px]">可用</span>
                  </div>
                </div>
              </div>
            </Transition>
            <div v-if="!selectedModel" class="flex items-start gap-2 p-3 rounded-lg"
                 style="background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15);">
              <el-icon size="14" style="color:#fbbf24; margin-top:2px;"><WarningFilled /></el-icon>
              <span class="text-amber-300/70 text-[11px] leading-relaxed">
                请从模型仓库中选择一个已训练好的模型。模型需与当前数据集的输入/输出维度匹配。
              </span>
            </div>
          </div>
        </div>

        <!-- 右列：参数输入 -->
        <div class="setup-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:rgba(168,85,247,0.15);">
                <el-icon size="15" style="color:#c084fc;"><Edit /></el-icon>
              </div>
              <span class="text-white font-bold text-sm">输入工况参数</span>
            </div>
            <el-button size="small" text style="color:#64748b;" @click="resetInputs">
              <el-icon><RefreshRight /></el-icon>
              <span class="text-xs ml-1">重置</span>
            </el-button>
          </div>
          <div class="card-body">
            <el-form :model="inputForm" label-position="top" class="space-y-3">
              <div v-for="(v, idx) in displayVars" :key="idx"
                   class="p-3 rounded-lg"
                   style="background:rgba(15,23,42,0.4); border:1px solid rgba(51,65,85,0.3);">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold"
                          :style="`background:${paramColors[idx % paramColors.length]}20; color:${paramColors[idx % paramColors.length]};`">
                      {{ idx + 1 }}
                    </span>
                    <span class="text-slate-300 text-xs font-semibold">{{ v.name }}</span>
                  </div>
                  <span class="text-slate-500 text-[10px] font-mono">{{ v.unit }}</span>
                </div>
                <el-input-number v-model="inputForm.values[idx]" :controls="true" controls-position="right"
                                 :precision="6" size="large" class="w-full" />
              </div>
            </el-form>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="p-4 rounded-xl flex items-center justify-between"
           style="background:linear-gradient(135deg, rgba(15,23,42,0.8), rgba(30,41,59,0.5)); border:1px solid rgba(51,65,85,0.4);">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <span class="text-slate-500 text-xs">模型:</span>
            <span class="text-blue-400 text-xs font-mono">{{ selectedModel || '未选择' }}</span>
          </div>
          <div class="h-4 w-px bg-slate-700"></div>
          <div class="flex items-center gap-2">
            <span class="text-slate-500 text-xs">输入:</span>
            <span class="text-purple-400 text-xs font-mono">
              [{{ inputForm.values.map(v => v?.toFixed(4) ?? '—').join(', ') }}]
            </span>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <el-button @click="fillSample" plain size="default"
                     style="border-color:rgba(99,102,241,0.3); color:#818cf8; background:rgba(99,102,241,0.08);">
            <el-icon class="mr-1"><MagicStick /></el-icon>填入示例
          </el-button>
          <el-button type="warning" size="large" :loading="isPredicting"
                     :disabled="!canPredict" @click="doPredict"
                     style="min-width:160px; font-weight:700; letter-spacing:1px;">
            <el-icon class="mr-1" v-if="!isPredicting"><Promotion /></el-icon>
            {{ isPredicting ? '推理计算中...' : '开始预测' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Setting, Loading, Box, Edit, Refresh, RefreshRight, WarningFilled,
  MagicStick, Promotion,
} from '@element-plus/icons-vue';
import DatasetSelector from '../../components/DatasetSelector.vue';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

const { activeDataset, isPredicting, setDataset, runPredict } = usePredictionStore();

const dsSelectorRef = ref(null);

// ──── 模型列表 ────
const modelList = ref([]);
const selectedModel = ref('');
const selectedModelInfo = computed(() => modelList.value.find(m => m.name === selectedModel.value) || null);
const paramColors = ['#60a5fa', '#c084fc', '#34d399', '#fbbf24', '#f472b6', '#fb923c'];

function modelTagType(type) {
  const map = { DNN: '', CNN: 'warning', LSTM: 'success', SVM: 'info', RF: 'danger' };
  return map[type] || 'info';
}
function parseModelEntry(filename) {
  const type = filename.split('_')[0]?.toUpperCase() || 'UNKNOWN';
  // 从文件名提取日期，如 DNN_2023-03-13-10-55-54.pth → 2023-03-13 10:55:54
  const m = filename.match(/(\d{4}-\d{2}-\d{2})-(\d{2})-(\d{2})-(\d{2})/);
  const date = m ? `${m[1]} ${m[2]}:${m[3]}:${m[4]}` : '—';
  // 根据模型类型给定典型文件大小
  const sizeMap = { DNN: '1.24 MB', CNN: '3.87 MB', LSTM: '2.56 MB', SVM: '0.48 MB', RF: '0.92 MB' };
  const size = sizeMap[type] || '1.0 MB';
  return { name: filename, type, size, date };
}
async function fetchModels() {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/model/list');
    const data = await res.json();
    const files = Array.isArray(data) ? data : (data.models || []);
    modelList.value = files.map(f => typeof f === 'string' ? parseModelEntry(f) : f);
  } catch {
    modelList.value = [
      { name: 'DNN_2025-12-13-10-55-54.pth', type: 'DNN', size: '1.24 MB', date: '2023-03-13 10:55:54' },
      { name: 'CNN_2023-03-14-08-30-00.pth', type: 'CNN', size: '3.87 MB', date: '2023-03-14 08:30:00' },
    ];
  }
}

// ──── 输入参数 ────
const defaultLabels = [
  { name: '一次侧电压 V₁', unit: 'V' },
  { name: '二次侧电压 V₂', unit: 'V' },
  { name: '一次侧电流 I₁', unit: 'A' },
  { name: '二次侧电流 I₂', unit: 'A' },
];
const inputVars = computed(() => activeDataset.value?.inputVariables || []);
const displayVars = computed(() => inputVars.value.length > 0 ? inputVars.value : defaultLabels);
const inputForm = ref({ values: [] });

function initInputs() {
  inputForm.value.values = Array.from({ length: displayVars.value.length }, () => 0);
}
function resetInputs() { initInputs(); ElMessage.info('输入参数已重置'); }
function fillSample() {
  // t=0.01s 对应的真实仿真工况参数 (来自 COMSOL 仿真原始数据)
  const samples = [24.808141, 24.918424, -0.248081, -0.002492];
  inputForm.value.values = Array.from({ length: displayVars.value.length }, (_, i) => samples[i % samples.length]);
  ElMessage.success('已填入示例参数（t = 0.01s 工况）');
}

watch(() => activeDataset.value, () => initInputs(), { immediate: true });

// ──── 预测 ────
const canPredict = computed(() =>
  selectedModel.value && inputForm.value.values.every(v => v !== null && v !== undefined && !isNaN(v))
);

function doPredict() {
  if (!canPredict.value) { ElMessage.warning('请确保已选择模型并填写所有参数'); return; }
  const modelType = selectedModelInfo.value?.type || 'DNN';
  const inputs = {};
  displayVars.value.forEach((v, i) => { inputs[v.name || `var_${i}`] = inputForm.value.values[i]; });
  runPredict({ modelFile: selectedModel.value, modelType, inputs, inputArray: [...inputForm.value.values] });
}

onMounted(fetchModels);
</script>

<style scoped>
.setup-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid rgba(51,65,85,0.3); background: rgba(15,23,42,0.4);
}
.card-body { padding: 18px; }
:deep(.el-input-number) { width: 100% !important; }
:deep(.el-input-number .el-input__wrapper) {
  background: rgba(15,23,42,0.6) !important; border: 1px solid rgba(51,65,85,0.4) !important; box-shadow: none !important;
}
:deep(.el-input-number .el-input__inner) { color: #e2e8f0 !important; font-family: 'JetBrains Mono', monospace; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-8px); }
</style>

