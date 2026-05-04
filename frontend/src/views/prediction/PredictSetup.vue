<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- ═══════ 页面标题 ═══════ -->
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
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">基于激活模型，填写工况参数，发起电磁场分布预测</p>
        </div>
        <div v-if="isPredicting" class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
             style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); color:#fbbf24;">
          <el-icon class="is-loading" size="12"><Loading /></el-icon>
          推理计算中...
        </div>
      </div>
    </div>

    <!-- ═══════ 主体内容 ═══════ -->
    <div class="px-6 pb-6 space-y-5">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">

        <!-- 左列：激活模型信息 -->
        <div class="setup-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:rgba(59,130,246,0.15);">
                <el-icon size="15" style="color:#60a5fa;"><Box /></el-icon>
              </div>
              <span class="text-white font-bold text-sm">当前激活模型</span>
            </div>
            <el-button size="small" text style="color:#64748b;" @click="refreshActiveModel">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="card-body space-y-4">
            <!-- 已激活 -->
            <div v-if="activeModel" class="p-4 rounded-xl space-y-3"
                 style="background:rgba(15,23,42,0.5); border:1px solid rgba(16,185,129,0.2);">
              <div class="flex items-center gap-2 mb-1">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
                <span class="text-emerald-400 text-xs font-bold">已激活</span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-slate-500">模型类型</span>
                  <div class="mt-0.5">
                    <el-tag size="small" :type="modelTagType(activeModel.type)" effect="dark" round>
                      {{ activeModel.type }}
                    </el-tag>
                  </div>
                </div>
                <div>
                  <span class="text-slate-500">输入维度</span>
                  <div class="text-white font-mono font-bold mt-0.5">{{ inputDim }}</div>
                </div>
                <div>
                  <span class="text-slate-500">输出维度</span>
                  <div class="text-white font-mono font-bold mt-0.5">{{ outputDim }}</div>
                </div>
                <div>
                  <span class="text-slate-500">ZScore归一化</span>
                  <div class="mt-0.5">
                    <el-tag size="small" :type="activeModel.metrics?.used_zscore ? 'success' : 'info'" effect="plain">
                      {{ activeModel.metrics?.used_zscore ? '是' : '否' }}
                    </el-tag>
                  </div>
                </div>
                <div>
                  <span class="text-slate-500">PCA降维</span>
                  <div class="mt-0.5">
                    <el-tag size="small" :type="activeModel.metrics?.used_pca ? 'success' : 'info'" effect="plain">
                      {{ activeModel.metrics?.used_pca ? '是' : '否' }}
                    </el-tag>
                  </div>
                </div>
                <div>
                  <span class="text-slate-500">测试损失</span>
                  <div class="text-amber-300 font-mono text-xs mt-0.5">
                    {{ fmtLoss(activeModel.metrics?.final_test_loss) }}
                  </div>
                </div>
              </div>
              <div class="pt-1 border-t border-slate-700/50">
                <span class="text-slate-500 text-[10px]">文件</span>
                <div class="text-slate-300 font-mono text-[10px] truncate mt-0.5">
                  {{ modelFilename }}
                </div>
              </div>
            </div>

            <!-- 未激活提示 -->
            <div v-else class="flex flex-col items-center justify-center py-10 space-y-3">
              <el-icon size="40" style="color:#334155;"><Box /></el-icon>
              <p class="text-slate-500 text-sm">尚未激活任何模型</p>
              <el-button size="small" type="primary" plain @click="goModelManage">
                前往模型管理激活模型
              </el-button>
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
              <el-tag v-if="activeModel" size="small" effect="plain" type="info">
                {{ inputDim }} 维
              </el-tag>
            </div>
            <el-button size="small" text style="color:#64748b;" @click="resetInputs">
              <el-icon><RefreshRight /></el-icon>
              <span class="text-xs ml-1">重置</span>
            </el-button>
          </div>
          <div class="card-body">
            <div v-if="!activeModel" class="flex items-center justify-center py-10 text-slate-600 text-sm">
              请先激活模型
            </div>
            <el-form v-else :model="inputForm" label-position="top" class="space-y-3">
              <div v-for="(label, idx) in inputLabels" :key="idx"
                   class="p-3 rounded-lg"
                   style="background:rgba(15,23,42,0.4); border:1px solid rgba(51,65,85,0.3);">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold"
                          :style="`background:${paramColors[idx % paramColors.length]}20; color:${paramColors[idx % paramColors.length]};`">
                      {{ idx + 1 }}
                    </span>
                    <span class="text-slate-300 text-xs font-semibold">{{ label }}</span>
                  </div>
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
            <span class="text-blue-400 text-xs font-mono">{{ activeModel ? `${activeModel.type} #${activeModel.id}` : '未激活' }}</span>
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
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  Setting, Loading, Box, Edit, Refresh, RefreshRight,
  MagicStick, Promotion,
} from '@element-plus/icons-vue';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

const router = useRouter();
const { isPredicting, runPredict } = usePredictionStore();

// ──── 激活模型 ────
const activeModel = ref(null);

function refreshActiveModel() {
  try {
    const raw = localStorage.getItem('active_model_info');
    activeModel.value = raw ? JSON.parse(raw) : null;
  } catch {
    activeModel.value = null;
  }
}

const modelFilename = computed(() =>
  activeModel.value?.file_path ? activeModel.value.file_path.split('/').pop() : '—'
);

const inputDim = computed(() =>
  activeModel.value?.metrics?.input_dim ?? activeModel.value?.metrics?.inputDim ?? 4
);
const outputDim = computed(() =>
  activeModel.value?.metrics?.output_dim ?? activeModel.value?.metrics?.outputDim ?? '—'
);

function modelTagType(type) {
  const map = { DNN: '', CNN: 'warning', RF: 'danger' };
  return map[type?.toUpperCase()] || 'info';
}
function fmtLoss(v) {
  if (v == null) return '—';
  return Number(v).toExponential(4);
}
function goModelManage() {
  router.push('/model-management');
}

// ──── 输入标签（优先读数据集 inputVariables，降级到泛型标签） ────
const datasetInputVars = ref([]);  // 从后端加载的数据集输入变量定义

async function loadDatasetVars(datasetId) {
  if (!datasetId) { datasetInputVars.value = []; return; }
  try {
    const token = localStorage.getItem('auth_token');
    const res = await fetch(`http://127.0.0.1:5000/api/dataset/${datasetId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      datasetInputVars.value = data.inputVariables || [];
    }
  } catch { datasetInputVars.value = []; }
}

watch(activeModel, (m) => {
  if (m?.dataset_id) loadDatasetVars(m.dataset_id);
  else datasetInputVars.value = [];
}, { immediate: true });

const inputLabels = computed(() => {
  const n = inputDim.value;
  return Array.from({ length: n }, (_, i) => {
    const v = datasetInputVars.value[i];
    if (v) return v.unit ? `${v.name} (${v.unit})` : v.name;
    return `输入变量 ${i + 1}`;
  });
});

const paramColors = ['#60a5fa', '#c084fc', '#34d399', '#fbbf24', '#f472b6', '#fb923c'];

// ──── 输入值 ────
const inputForm = ref({ values: [] });

function initInputs() {
  inputForm.value.values = Array.from({ length: inputDim.value }, () => 0);
}
function resetInputs() { initInputs(); ElMessage.info('输入参数已重置'); }
function fillSample() {
  // 示例值：若数据集只有1个输入（如电抗器电流），只填1个
  const samples = [24.808141, 24.918424, -0.248081, -0.002492];
  inputForm.value.values = Array.from({ length: inputDim.value }, (_, i) => samples[i % samples.length]);
  ElMessage.success('已填入示例参数');
}

watch(inputDim, () => initInputs(), { immediate: true });

// ──── 预测 ────
const canPredict = computed(() =>
  activeModel.value &&
  inputForm.value.values.length === inputDim.value &&
  inputForm.value.values.every(v => v !== null && v !== undefined && !isNaN(v))
);

function doPredict() {
  if (!canPredict.value) {
    if (!activeModel.value) { ElMessage.warning('请先在「模型管理」中激活一个模型'); return; }
    ElMessage.warning('请确保已填写所有输入参数');
    return;
  }
  runPredict({
    modelInfo:   activeModel.value,
    inputArray:  [...inputForm.value.values],
    inputLabels: inputLabels.value,
  });
}

onMounted(refreshActiveModel);
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
</style>

