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
            模型仓库
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理已保存的模型权重文件</p>
      </div>
      <button @click="fetchModels"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
              style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.3); color:#e2e8f0;">
        <el-icon><Refresh /></el-icon>刷新列表
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
      <el-input v-model="searchText" placeholder="搜索模型名称..." size="small" clearable
                style="width:220px; --el-input-bg-color:rgba(10,18,36,0.9); --el-input-text-color:#e2e8f0; --el-input-border-color:rgba(51,65,85,0.5);">
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
      <span class="ml-auto text-xs text-slate-600 font-mono">共 {{ filteredModels.length }} 个模型</span>
    </div>

    <!-- Model Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" v-loading="loading">
      <div v-for="model in pagedModels" :key="model.name"
           class="rounded-xl p-4 space-y-3 transition-all duration-200 hover:scale-[1.015]"
           :style="`background:rgba(10,18,36,0.92); border:1px solid ${model.active ? ts(model.type).border : 'rgba(51,65,85,0.35)'};
                    ${model.active ? `box-shadow:0 0 22px ${ts(model.type).glow};` : ''}`">

        <!-- Header: name + active badge -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <el-icon class="flex-shrink-0" :style="`color:${ts(model.type).color};`" size="14"><Box /></el-icon>
            <span class="font-mono text-[11px] text-slate-300 truncate" :title="model.name">{{ model.name }}</span>
          </div>
          <span v-if="model.active"
                class="flex-shrink-0 flex items-center gap-1 text-[9px] px-2 py-0.5 rounded-full font-bold whitespace-nowrap"
                style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>已激活
          </span>
        </div>

        <!-- Type + File Info -->
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[11px] font-bold px-2 py-0.5 rounded"
                :style="`background:${ts(model.type).bg}; color:${ts(model.type).color}; border:1px solid ${ts(model.type).border};`">
            {{ model.type }}
          </span>
          <span class="text-[10px] text-slate-500 font-mono">{{ model.size }}</span>
          <span class="text-[10px] text-slate-600">{{ model.date }}</span>
          <span class="ml-auto text-[9px] px-1.5 py-0.5 rounded text-slate-500"
                style="background:rgba(51,65,85,0.3); border:1px solid rgba(51,65,85,0.4);">
            {{ model.framework }}
          </span>
        </div>

        <!-- Best Metrics -->
        <div class="p-2.5 rounded-lg" style="background:rgba(2,8,23,0.55); border:1px solid rgba(51,65,85,0.3);">
          <div class="text-[9px] uppercase tracking-widest text-slate-600 font-bold mb-1.5">最佳评估指标 · 测试集</div>
          <div class="grid grid-cols-3 gap-1.5">
            <div class="text-center p-1.5 rounded" style="background:rgba(14,165,233,0.07); border:1px solid rgba(14,165,233,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">MAE (T)</div>
              <div class="text-xs font-mono font-bold text-sky-300">{{ model.metrics.mae }}</div>
            </div>
            <div class="text-center p-1.5 rounded" style="background:rgba(236,72,153,0.07); border:1px solid rgba(236,72,153,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">RMSE (T)</div>
              <div class="text-xs font-mono font-bold text-pink-300">{{ model.metrics.rmse }}</div>
            </div>
            <div class="text-center p-1.5 rounded" style="background:rgba(16,185,129,0.07); border:1px solid rgba(16,185,129,0.15);">
              <div class="text-[9px] text-slate-500 mb-0.5">R²</div>
              <div class="text-xs font-mono font-bold text-emerald-300">{{ model.metrics.r2 }}</div>
            </div>
          </div>
          <!-- R² 进度条 -->
          <div class="mt-2">
            <div class="h-1 rounded-full overflow-hidden" style="background:rgba(51,65,85,0.4);">
              <div class="h-full rounded-full transition-all duration-500"
                   :style="`width:${(parseFloat(model.metrics.r2)*100).toFixed(1)}%;
                            background:linear-gradient(90deg,${ts(model.type).color},${ts(model.type).color}88);`"></div>
            </div>
            <div class="flex justify-between text-[9px] mt-0.5">
              <span class="text-slate-600">R² 拟合度</span>
              <span :style="`color:${ts(model.type).color};`" class="font-mono">{{ (parseFloat(model.metrics.r2)*100).toFixed(2) }}%</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-0.5">
          <button @click="downloadModel(model)"
                  class="flex-1 text-[11px] py-1.5 rounded-lg transition-all hover:opacity-80 font-semibold"
                  style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.3); color:#60a5fa;">
            下载
          </button>
          <button @click="deployModel(model)" :disabled="model.active"
                  class="flex-1 text-[11px] py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40 font-semibold"
                  style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399;">
            {{ model.active ? '已激活' : '激活' }}
          </button>
          <button @click="deleteModel(model)"
                  class="flex-1 text-[11px] py-1.5 rounded-lg transition-all hover:opacity-80 font-semibold"
                  style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#f87171;">
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center pt-1">
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

// ---- Type style map ----
const TYPE_STYLES = {
  DNN:  { color:'#60a5fa', bg:'rgba(59,130,246,0.1)',   border:'rgba(59,130,246,0.4)',  glow:'rgba(59,130,246,0.12)'  },
  CNN:  { color:'#818cf8', bg:'rgba(99,102,241,0.1)',   border:'rgba(99,102,241,0.4)',  glow:'rgba(99,102,241,0.12)'  },
  RF:   { color:'#fbbf24', bg:'rgba(245,158,11,0.1)',   border:'rgba(245,158,11,0.4)',  glow:'rgba(245,158,11,0.12)'  },
};
const ts = (type) => TYPE_STYLES[type] || TYPE_STYLES.DNN;

// ---- 8 Mock Models（指标来源：表3-4 单相变压器磁场预测结果）----
const allModels = ref([
  {
    name: 'DNN_2025-07-25-19-28-48.pth', type: 'DNN', size: '1.24 MB',
    date: '2025-07-25 19:28', framework: 'PyTorch', active: true,
    metrics: { mae: '0.0229', rmse: '0.0149', r2: '0.9924' },
  },
  {
    name: 'CNN_2025-07-20-11-43-05.pth', type: 'CNN', size: '1.83 MB',
    date: '2025-07-20 11:43', framework: 'PyTorch', active: false,
    metrics: { mae: '0.0613', rmse: '0.0271', r2: '0.9921' },
  },
  {
    name: 'DNN_2025-07-14-09-16-33.pth', type: 'DNN', size: '1.24 MB',
    date: '2025-07-14 09:16', framework: 'PyTorch', active: false,
    metrics: { mae: '0.0276', rmse: '0.0183', r2: '0.9889' },
  },
  {
    name: 'CNN_2025-07-10-16-22-41.pth', type: 'CNN', size: '1.83 MB',
    date: '2025-07-10 16:22', framework: 'PyTorch', active: false,
    metrics: { mae: '0.0724', rmse: '0.0318', r2: '0.9864' },
  },
  {
    name: 'RF_2025-07-07-10-05-31.pkl',  type: 'RF',  size: '0.63 MB',
    date: '2025-07-07 10:05', framework: 'Sklearn',  active: false,
    metrics: { mae: '0.1500', rmse: '0.2600', r2: '0.9700' },
  },
  {
    name: 'DNN_2025-07-02-14-37-22.pth', type: 'DNN', size: '1.24 MB',
    date: '2025-07-02 14:37', framework: 'PyTorch', active: false,
    metrics: { mae: '0.0348', rmse: '0.0241', r2: '0.9843' },
  },
  {
    name: 'CNN_2025-06-28-20-09-17.pth', type: 'CNN', size: '1.83 MB',
    date: '2025-06-28 20:09', framework: 'PyTorch', active: false,
    metrics: { mae: '0.0851', rmse: '0.0394', r2: '0.9802' },
  },
  {
    name: 'RF_2025-06-24-08-15-44.pkl',  type: 'RF',  size: '0.63 MB',
    date: '2025-06-24 08:15', framework: 'Sklearn',  active: false,
    metrics: { mae: '0.1783', rmse: '0.2942', r2: '0.9583' },
  },
]);

// ---- State ----
const loading = ref(false);
const searchText = ref('');
const activeType = ref('all');
const currentPage = ref(1);
const pageSize = ref(6);

// ---- Type filter config ----
const typeFilters = [
  { key:'all',  label:'全部',  activeBg:'rgba(71,85,105,0.3)',   color:'#cbd5e1', border:'rgba(71,85,105,0.6)'   },
  { key:'DNN',  label:'DNN',  activeBg:'rgba(59,130,246,0.15)',  color:'#60a5fa', border:'rgba(59,130,246,0.5)'  },
  { key:'CNN',  label:'CNN',  activeBg:'rgba(99,102,241,0.15)',  color:'#818cf8', border:'rgba(99,102,241,0.5)'  },
  { key:'RF',   label:'RF',   activeBg:'rgba(245,158,11,0.15)',  color:'#fbbf24', border:'rgba(245,158,11,0.5)'  },
];

const setType = (key) => {
  activeType.value = (activeType.value === key && key !== 'all') ? 'all' : key;
  currentPage.value = 1;
};

// ---- Computed ----
const filteredModels = computed(() => {
  let list = allModels.value;
  if (activeType.value !== 'all') list = list.filter(m => m.type === activeType.value);
  if (searchText.value.trim()) {
    const kw = searchText.value.toLowerCase();
    list = list.filter(m => m.name.toLowerCase().includes(kw));
  }
  return list;
});

const pagedModels = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredModels.value.slice(start, start + pageSize.value);
});

const stats = computed(() => {
  const ms = allModels.value;
  const bestR2  = Math.max(...ms.map(m => parseFloat(m.metrics.r2)));
  const bestMAE = Math.min(...ms.map(m => parseFloat(m.metrics.mae)));
  return [
    { label:'模型总数',     value: ms.length,             color:'#60a5fa', bg:'rgba(59,130,246,0.07)',  border:'rgba(59,130,246,0.2)',  iconBg:'rgba(59,130,246,0.15)',  icon: Box          },
    { label:'已激活',       value: ms.filter(m=>m.active).length, color:'#34d399', bg:'rgba(16,185,129,0.07)', border:'rgba(16,185,129,0.2)', iconBg:'rgba(16,185,129,0.15)', icon: Connection   },
    { label:'最优 R²',      value: bestR2.toFixed(4),     color:'#c084fc', bg:'rgba(168,85,247,0.07)', border:'rgba(168,85,247,0.2)',  iconBg:'rgba(168,85,247,0.15)', icon: DataAnalysis },
    { label:'最优 MAE (T)', value: bestMAE.toFixed(4),    color:'#fbbf24', bg:'rgba(245,158,11,0.07)', border:'rgba(245,158,11,0.2)',  iconBg:'rgba(245,158,11,0.15)', icon: Odometer      },
  ];
});

// ---- Actions ----
const fetchModels = () => {
  loading.value = true;
  setTimeout(() => { loading.value = false; }, 400);
};

const deployModel = (model) => {
  if (model.active) return;
  allModels.value.forEach(m => (m.active = false));
  model.active = true;
  ElMessage.success({ message: `模型 ${model.name} 已成功激活，用于实时推理`, duration: 2500 });
};

const downloadModel = (model) => {
  ElMessage.info(`正在准备下载 ${model.name}...`);
};

const deleteModel = (model) => {
  if (model.active) { ElMessage.warning('激活中的模型不可删除，请先切换激活模型'); return; }
  ElMessageBox.confirm(`确定要删除模型 ${model.name} 吗？此操作不可恢复。`, '删除确认', {
    confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning',
  }).then(() => {
    allModels.value = allModels.value.filter(m => m.name !== model.name);
    ElMessage.success('模型已从仓库中删除');
  }).catch(() => {});
};

onMounted(fetchModels);
</script>

<style scoped>
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: #3b82f6;
}
:deep(.el-pagination.is-background .el-pager li) {
  background-color: rgba(10,18,36,0.9);
  color: #64748b;
  border: 1px solid rgba(51,65,85,0.4);
}
:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) {
  background-color: rgba(10,18,36,0.9);
  color: #64748b;
  border: 1px solid rgba(51,65,85,0.4);
}
:deep(.el-pagination__total) { color: #64748b; }
</style>
