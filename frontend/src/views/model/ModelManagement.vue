<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#b45309,#f59e0b); box-shadow:0 0 20px rgba(245,158,11,0.4);">
            <el-icon size="20" style="color:white;"><Box /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#fbbf24,#fde68a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            训练任务记录
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">历史训练任务追溯 · 模型文件管理 · 指标对比</p>
      </div>
      <button @click="fetchModels"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
              style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.3); color:#e2e8f0;">
        <el-icon><Refresh /></el-icon>刷新
      </button>
    </div>

    <!-- Stats Bar -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="stat in stats" :key="stat.label"
           class="p-4 rounded-xl flex items-center gap-3"
           :style="`background:${stat.bg}; border:1px solid ${stat.border};`">
        <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
             :style="`background:${stat.iconBg};`">
          <el-icon size="18" :style="`color:${stat.color};`"><component :is="stat.icon" /></el-icon>
        </div>
        <div>
          <div class="text-lg font-black font-mono leading-none" :style="`color:${stat.color};`">{{ stat.value }}</div>
          <div class="text-[10px] text-slate-500 mt-0.5">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex items-center gap-3 flex-wrap">
      <el-input v-model="searchText" placeholder="搜索数据集 / 文件名..." size="small" clearable
                style="width:240px; --el-input-bg-color:rgba(10,18,36,0.9); --el-input-text-color:#e2e8f0; --el-input-border-color:rgba(51,65,85,0.5);">
        <template #prefix><el-icon class="text-slate-500"><Search /></el-icon></template>
      </el-input>
      <div class="flex gap-2 flex-wrap">
        <button v-for="t in typeFilters" :key="t.key" @click="setType(t.key)"
                class="px-3 py-1 rounded-lg text-xs font-semibold transition-all"
                :style="activeType === t.key
                  ? `background:${t.activeBg}; color:${t.color}; border:1px solid ${t.border};`
                  : 'background:rgba(30,41,59,0.6); color:#64748b; border:1px solid rgba(51,65,85,0.4);'">
          {{ t.label }}
        </button>
      </div>
      <span class="ml-auto text-xs text-slate-600 font-mono">共 {{ filteredModels.length }} 条记录</span>
    </div>

    <!-- Empty -->
    <div v-if="!loading && filteredModels.length === 0"
         class="flex flex-col items-center justify-center py-20 text-slate-600">
      <el-icon size="48" class="mb-3 opacity-30"><Box /></el-icon>
      <p class="text-sm">暂无训练记录，请前往「训练任务调度」启动训练</p>
    </div>

    <!-- Model Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" v-loading="loading">
      <div v-for="model in pagedModels" :key="model.id"
           class="rounded-xl p-4 space-y-3 transition-all duration-200 hover:scale-[1.015]"
           :style="`background:rgba(10,18,36,0.92);
                    border:1px solid ${model.id === activeModelId ? ts(model.model_type).border : (model.status==='failed' ? 'rgba(239,68,68,0.3)' : 'rgba(51,65,85,0.35)')};
                    ${model.id === activeModelId ? `box-shadow:0 0 22px ${ts(model.model_type).glow};` : ''}`">

        <!-- Header -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <el-icon class="flex-shrink-0" :style="`color:${ts(model.model_type).color};`" size="14"><Box /></el-icon>
            <span class="font-mono text-[11px] text-slate-300 truncate" :title="modelFilename(model)">
              {{ modelFilename(model) }}
            </span>
          </div>
          <!-- Status badge -->
          <span v-if="model.status === 'done' && model.id === activeModelId"
                class="flex-shrink-0 flex items-center gap-1 text-[9px] px-2 py-0.5 rounded-full font-bold whitespace-nowrap"
                style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>已激活
          </span>
          <span v-else-if="model.status === 'training'"
                class="flex-shrink-0 flex items-center gap-1 text-[9px] px-2 py-0.5 rounded-full font-bold whitespace-nowrap"
                style="background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3);">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse inline-block"></span>训练中
          </span>
          <span v-else-if="model.status === 'failed'"
                class="flex-shrink-0 text-[9px] px-2 py-0.5 rounded-full font-bold whitespace-nowrap"
                style="background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3);">
            失败
          </span>
        </div>

        <!-- Type + Dataset + Date -->
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[11px] font-bold px-2 py-0.5 rounded"
                :style="`background:${ts(model.model_type).bg}; color:${ts(model.model_type).color}; border:1px solid ${ts(model.model_type).border};`">
            {{ model.model_type }}
          </span>
          <span class="text-[10px] text-slate-400 truncate max-w-[120px]" :title="model.dataset_name || model.dataset_id">
            📁 {{ model.dataset_name || model.dataset_id }}
          </span>
          <span class="ml-auto text-[10px] text-slate-600 whitespace-nowrap">{{ model.created_at }}</span>
        </div>

        <!-- Config chips -->
        <div v-if="model.config" class="flex flex-wrap gap-1">
          <span v-if="model.config.epochs" class="text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(51,65,85,0.4); color:#94a3b8; border:1px solid rgba(51,65,85,0.5);">
            Epochs {{ model.config.epochs }}
          </span>
          <span v-if="model.config.learning_rate" class="text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(51,65,85,0.4); color:#94a3b8; border:1px solid rgba(51,65,85,0.5);">
            LR {{ model.config.learning_rate }}
          </span>
          <span v-if="model.config.batch_size" class="text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(51,65,85,0.4); color:#94a3b8; border:1px solid rgba(51,65,85,0.5);">
            BS {{ model.config.batch_size }}
          </span>
          <span v-if="model.config.n_estimators" class="text-[9px] px-1.5 py-0.5 rounded"
                style="background:rgba(51,65,85,0.4); color:#94a3b8; border:1px solid rgba(51,65,85,0.5);">
            Trees {{ model.config.n_estimators }}
          </span>
        </div>

        <!-- Metrics (only for done) -->
        <div v-if="model.status === 'done' && model.metrics" class="p-2.5 rounded-lg"
             style="background:rgba(2,8,23,0.55); border:1px solid rgba(51,65,85,0.3);">
          <div class="text-[9px] uppercase tracking-widest text-slate-600 font-bold mb-1.5">测试集指标</div>
          <div class="grid grid-cols-3 gap-1.5">
            <div class="text-center p-1.5 rounded" style="background:rgba(14,165,233,0.07); border:1px solid rgba(14,165,233,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">Train Loss</div>
              <div class="text-xs font-mono font-bold text-sky-300">{{ fmt(model.metrics.final_train_loss) }}</div>
            </div>
            <div class="text-center p-1.5 rounded" style="background:rgba(236,72,153,0.07); border:1px solid rgba(236,72,153,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">Test Loss</div>
              <div class="text-xs font-mono font-bold text-pink-300">{{ fmt(model.metrics.final_test_loss) }}</div>
            </div>
            <div class="text-center p-1.5 rounded" style="background:rgba(16,185,129,0.07); border:1px solid rgba(16,185,129,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">Dim</div>
              <div class="text-xs font-mono font-bold text-emerald-300">
                {{ model.metrics.input_dim }}→{{ model.metrics.output_dim }}
              </div>
            </div>
          </div>
        </div>

        <!-- Failed hint -->
        <div v-if="model.status === 'failed'"
             class="p-2.5 rounded-lg text-[10px] text-red-400"
             style="background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.2);">
          训练失败，请检查数据集预处理是否完整
        </div>

        <!-- Training hint -->
        <div v-if="model.status === 'training'"
             class="p-2.5 rounded-lg text-[10px] text-blue-400"
             style="background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.2);">
          训练进行中，请在「训练任务调度」页面查看进度
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-0.5">
          <button v-if="model.status === 'done'" @click="activateModel(model)"
                  :disabled="model.id === activeModelId"
                  class="flex-1 text-[11px] py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40 font-semibold"
                  style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399;">
            {{ model.id === activeModelId ? '已激活' : '激活用于预测' }}
          </button>
          <button @click="confirmDelete(model)"
                  class="flex-1 text-[11px] py-1.5 rounded-lg transition-all hover:opacity-80 font-semibold"
                  style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#f87171;">
            删除记录
          </button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center pt-1" v-if="filteredModels.length > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredModels.length"
        layout="prev, pager, next, total"
        background
      />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Refresh, Box, Search, Connection, DataAnalysis, Odometer } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';

const TYPE_STYLES = {
  DNN:  { color:'#60a5fa', bg:'rgba(59,130,246,0.1)',  border:'rgba(59,130,246,0.4)', glow:'rgba(59,130,246,0.12)' },
  CNN:  { color:'#818cf8', bg:'rgba(99,102,241,0.1)',  border:'rgba(99,102,241,0.4)', glow:'rgba(99,102,241,0.12)' },
  RF:   { color:'#fbbf24', bg:'rgba(245,158,11,0.1)',  border:'rgba(245,158,11,0.4)', glow:'rgba(245,158,11,0.12)' },
};
const ts = (type) => TYPE_STYLES[type?.toUpperCase()] || TYPE_STYLES.DNN;

const allModels = ref([]);
const loading   = ref(false);
const searchText  = ref('');
const activeType  = ref('all');
const currentPage = ref(1);
const pageSize    = ref(6);

// 激活的 model id，存 localStorage 供预测模块读取
const activeModelId = ref(parseInt(localStorage.getItem('active_model_id') || '0'));

const typeFilters = [
  { key:'all', label:'全部', activeBg:'rgba(71,85,105,0.3)',  color:'#cbd5e1', border:'rgba(71,85,105,0.6)' },
  { key:'DNN', label:'DNN', activeBg:'rgba(59,130,246,0.15)', color:'#60a5fa', border:'rgba(59,130,246,0.5)' },
  { key:'CNN', label:'CNN', activeBg:'rgba(99,102,241,0.15)', color:'#818cf8', border:'rgba(99,102,241,0.5)' },
  { key:'RF',  label:'RF',  activeBg:'rgba(245,158,11,0.15)', color:'#fbbf24', border:'rgba(245,158,11,0.5)' },
];

const setType = (key) => {
  activeType.value = (activeType.value === key && key !== 'all') ? 'all' : key;
  currentPage.value = 1;
};

const filteredModels = computed(() => {
  let list = allModels.value;
  if (activeType.value !== 'all') list = list.filter(m => m.model_type === activeType.value);
  if (searchText.value.trim()) {
    const kw = searchText.value.toLowerCase();
    list = list.filter(m =>
      (m.dataset_name || '').toLowerCase().includes(kw) ||
      (m.file_path || '').toLowerCase().includes(kw) ||
      (m.model_type || '').toLowerCase().includes(kw)
    );
  }
  return list;
});

const pagedModels = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredModels.value.slice(start, start + pageSize.value);
});

const stats = computed(() => {
  const ms = allModels.value;
  const done = ms.filter(m => m.status === 'done');
  const bestLoss = done.length
    ? Math.min(...done.map(m => m.metrics?.final_test_loss ?? Infinity)).toFixed(6)
    : '--';
  return [
    { label:'训练记录总数', value: ms.length,                    color:'#60a5fa', bg:'rgba(59,130,246,0.07)',  border:'rgba(59,130,246,0.2)',  iconBg:'rgba(59,130,246,0.15)',  icon: Box          },
    { label:'已完成',       value: done.length,                  color:'#34d399', bg:'rgba(16,185,129,0.07)', border:'rgba(16,185,129,0.2)',  iconBg:'rgba(16,185,129,0.15)', icon: Connection   },
    { label:'训练中',       value: ms.filter(m=>m.status==='training').length, color:'#60a5fa', bg:'rgba(59,130,246,0.07)', border:'rgba(59,130,246,0.2)', iconBg:'rgba(59,130,246,0.15)', icon: DataAnalysis },
    { label:'最优测试损失', value: bestLoss,                     color:'#fbbf24', bg:'rgba(245,158,11,0.07)', border:'rgba(245,158,11,0.2)',  iconBg:'rgba(245,158,11,0.15)', icon: Odometer      },
  ];
});

const modelFilename = (m) => {
  if (m.file_path) return m.file_path.split(/[/\\]/).pop();
  return `${m.model_type}_#${m.id}`;
};

const fmt = (v) => (v != null ? Number(v).toExponential(4) : '--');

const fetchModels = async () => {
  loading.value = true;
  try {
    const token = localStorage.getItem('auth_token');
    const resp = await fetch('http://127.0.0.1:5000/api/model/list', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) throw new Error(resp.statusText);
    const data = await resp.json();
    allModels.value = data.models || [];
  } catch (e) {
    ElMessage.error(`加载失败：${e.message}`);
  } finally {
    loading.value = false;
  }
};

const activateModel = async (model) => {
  activeModelId.value = model.id;
  localStorage.setItem('active_model_id', model.id);

  // 尝试拉取数据集 outputVariable 信息（用于预测结果页动态显示单位/标签）
  let outputUnit = 'T', outputLabel = 'B', deviceType = '', fieldType = '', coordSystem = 'xyz';
  try {
    const token = localStorage.getItem('auth_token');
    const dsResp = await fetch(`http://127.0.0.1:5000/api/dataset/${model.dataset_id}`,
      { headers: { Authorization: `Bearer ${token}` } });
    if (dsResp.ok) {
      const dsData = await dsResp.json();
      const ds = dsData.dataset || {};
      outputUnit  = ds.outputVariable?.unit  || 'T';
        outputLabel = ds.outputVariable?.name  || 'B';
        deviceType  = ds.deviceType || '';
        fieldType   = ds.fieldType  || '';
        coordSystem = ds.coordSystem || 'xyz';
    }
  } catch { /* 非致命，保持默认值 */ }

  localStorage.setItem('active_model_info', JSON.stringify({
    id: model.id,
    type: model.model_type,
    file_path: model.file_path,
    dataset_id: model.dataset_id,
    dataset_name: model.dataset_name || model.dataset_id,
    metrics: model.metrics,
    outputUnit,
    outputLabel,
    deviceType,
    fieldType,
    coordSystem,
  }));
  ElMessage.success(`模型 ${modelFilename(model)} 已激活，可在预测模块中使用`);
};

const confirmDelete = (model) => {
  ElMessageBox.confirm(
    `确定删除「${modelFilename(model)}」的训练记录？模型文件也将一并删除。`,
    '删除确认',
    { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const resp = await fetch(`http://127.0.0.1:5000/api/model/${model.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error((await resp.json()).error);
      allModels.value = allModels.value.filter(m => m.id !== model.id);
      if (activeModelId.value === model.id) {
        activeModelId.value = 0;
        localStorage.removeItem('active_model_id');
        localStorage.removeItem('active_model_info');
      }
      ElMessage.success('记录已删除');
    } catch (e) {
      ElMessage.error(`删除失败：${e.message}`);
    }
  }).catch(() => {});
};

onMounted(fetchModels);
</script>

<style scoped>
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) { background-color: #3b82f6; }
:deep(.el-pagination.is-background .el-pager li) { background-color: rgba(10,18,36,0.9); color: #64748b; border: 1px solid rgba(51,65,85,0.4); }
:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) { background-color: rgba(10,18,36,0.9); color: #64748b; border: 1px solid rgba(51,65,85,0.4); }
:deep(.el-pagination__total) { color: #64748b; }
</style>
