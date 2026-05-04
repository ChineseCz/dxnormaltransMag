<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#059669,#10b981); box-shadow:0 0 20px rgba(16,185,129,0.4);">
            <el-icon size="20" style="color:white;"><TrendCharts /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#34d399,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            训练结果
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">选择已完成的训练任务，查看损失曲线与超参配置</p>
      </div>
      <button @click="fetchModels"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
              style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.3); color:#e2e8f0;">
        <el-icon><Refresh /></el-icon>刷新
      </button>
    </div>

    <!-- 分页表格选择器 -->
    <div class="rounded-xl overflow-hidden" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <div class="px-4 pt-4 pb-2 flex items-center justify-between">
        <span class="text-xs text-slate-400 font-semibold uppercase tracking-widest">选择训练任务</span>
        <span class="text-xs text-slate-600 font-mono">{{ doneModels.length }} 条已完成记录</span>
      </div>

      <div v-if="doneModels.length === 0 && !loading" class="px-4 pb-4 text-slate-600 text-sm">
        暂无已完成的训练记录，请先前往「训练任务」完成训练
      </div>

      <el-table v-else :data="pagedDone" size="small" v-loading="loading"
                highlight-current-row @current-change="select"
                :row-class-name="({row}) => row.id === selected?.id ? 'selected-row' : ''"
                style="background:transparent; --el-table-bg-color:transparent; --el-table-tr-bg-color:transparent;
                       --el-table-header-bg-color:rgba(2,8,23,0.6); --el-table-header-text-color:#64748b;
                       --el-table-text-color:#cbd5e1; --el-table-border-color:rgba(51,65,85,0.3);
                       --el-table-row-hover-bg-color:rgba(59,130,246,0.06);">
        <el-table-column label="模型文件" min-width="200">
          <template #default="{row}">
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-bold px-1.5 py-0.5 rounded"
                    :style="`background:${ts(row.model_type).bg}; color:${ts(row.model_type).color}; border:1px solid ${ts(row.model_type).border};`">
                {{ row.model_type }}
              </span>
              <span class="font-mono text-xs text-slate-300 truncate">{{ modelName(row) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="数据集" width="120">
          <template #default="{row}">
            <span class="text-xs text-slate-400 truncate">{{ row.dataset_name || row.dataset_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Train Loss" width="110">
          <template #default="{row}">
            <span class="font-mono text-xs text-sky-300">{{ fmtE(row.metrics?.final_train_loss) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Test Loss" width="110">
          <template #default="{row}">
            <span class="font-mono text-xs text-pink-300">{{ fmtE(row.metrics?.final_test_loss) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="训练时间" width="140">
          <template #default="{row}">
            <span class="text-xs text-slate-500">{{ row.created_at }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end px-4 py-2" v-if="doneModels.length > tablePageSize">
        <el-pagination v-model:current-page="tablePage" :page-size="tablePageSize"
                       :total="doneModels.length" layout="prev, pager, next" small background />
      </div>
    </div>

    <!-- No selection placeholder -->
    <div v-if="!selected" class="flex flex-col items-center justify-center py-20 text-slate-700">
      <el-icon size="56" class="mb-4 opacity-20"><TrendCharts /></el-icon>
      <p class="text-sm">请在上方表格中点击一行查看结果</p>
    </div>

    <template v-if="selected">

      <!-- Metric cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="card in metricCards" :key="card.label"
             class="p-4 rounded-xl flex flex-col gap-1"
             :style="`background:${card.bg}; border:1px solid ${card.border};`">
          <div class="text-[10px] uppercase tracking-widest text-slate-500 font-bold">{{ card.label }}</div>
          <div class="text-xl font-black font-mono leading-none" :style="`color:${card.color};`">{{ card.value }}</div>
          <div class="text-[10px] text-slate-600">{{ card.hint }}</div>
        </div>
      </div>

      <!-- Loss 曲线图 -->
      <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.3);">
        <div class="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">训练损失曲线</div>
        <div v-if="hasLossHistory" style="height:280px;">
          <v-chart :option="lossChartOption" autoresize />
        </div>
        <div v-else class="flex items-center justify-center text-slate-600 text-xs" style="height:100px;">
          此记录无历史曲线（旧版训练任务未存储逐 epoch 数据）
        </div>
      </div>

      <!-- Config + Data grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 超参配置 -->
        <div class="p-4 rounded-xl space-y-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.3);">
          <div class="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">超参数配置</div>
          <template v-if="isDL">
            <div class="config-row"><span>模型类型</span><span>{{ selected.model_type }}</span></div>
            <div class="config-row"><span>Epochs</span><span>{{ selected.config?.epochs ?? '--' }}</span></div>
            <div class="config-row"><span>Batch Size</span><span>{{ selected.config?.batch_size ?? '--' }}</span></div>
            <div class="config-row"><span>Learning Rate</span><span>{{ selected.config?.learning_rate ?? '--' }}</span></div>
            <div v-if="selected.config?.hidden_layers?.length" class="config-row">
              <span>隐藏层</span><span>{{ selected.config.hidden_layers.map(l=>l.units||l).join(' → ') }}</span>
            </div>
          </template>
          <template v-else>
            <div class="config-row"><span>模型类型</span><span>随机森林 RF</span></div>
            <div class="config-row"><span>Trees</span><span>{{ selected.config?.n_estimators ?? '--' }}</span></div>
            <div class="config-row"><span>Max Depth</span><span>{{ selected.config?.max_depth ?? '--' }}</span></div>
          </template>
        </div>

        <!-- 数据规格 + 泛化诊断 -->
        <div class="p-4 rounded-xl space-y-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.3);">
          <div class="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">数据规格</div>
          <div class="config-row"><span>关联数据集</span><span>{{ selected.dataset_name || selected.dataset_id }}</span></div>
          <div class="config-row"><span>输入维度</span><span>{{ selected.metrics?.input_dim ?? '--' }}</span></div>
          <div class="config-row"><span>输出维度 (PCA)</span><span>{{ selected.metrics?.output_dim ?? '--' }}</span></div>
          <div class="config-row"><span>训练时间</span><span>{{ selected.created_at }}</span></div>
          <div v-if="selected.metrics" class="config-row">
            <span>泛化比率</span>
            <span :style="`color:${genRatio < 2 ? '#34d399' : genRatio < 5 ? '#fbbf24' : '#f87171'}`">
              {{ genRatio.toFixed(2) }}× {{ genRatio < 2 ? '✓ 泛化良好' : genRatio < 5 ? '△ 轻微过拟合' : '✗ 过拟合' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 跳转提示 -->
      <div class="flex items-center gap-3 p-4 rounded-xl"
           style="background:rgba(59,130,246,0.05); border:1px solid rgba(59,130,246,0.15);">
        <el-icon class="text-blue-400" size="16"><InfoFilled /></el-icon>
        <span class="text-xs text-slate-400">
          若要使用此模型进行推理预测，请前往
          <router-link to="/model-management" class="text-blue-400 underline underline-offset-2">模型中心</router-link>
          将其激活，再到
          <router-link to="/predict-setup" class="text-blue-400 underline underline-offset-2">实时预测</router-link>
          模块使用。
        </span>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { TrendCharts, Refresh, InfoFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

const TYPE_STYLES = {
  DNN: { color:'#60a5fa', bg:'rgba(59,130,246,0.1)',  border:'rgba(59,130,246,0.4)' },
  CNN: { color:'#818cf8', bg:'rgba(99,102,241,0.1)',  border:'rgba(99,102,241,0.4)' },
  RF:  { color:'#fbbf24', bg:'rgba(245,158,11,0.1)',  border:'rgba(245,158,11,0.4)' },
};
const ts = (t) => TYPE_STYLES[t?.toUpperCase()] || TYPE_STYLES.DNN;

const allModels  = ref([]);
const loading    = ref(false);
const selected   = ref(null);
const tablePage  = ref(1);
const tablePageSize = 8;

const doneModels = computed(() => allModels.value.filter(m => m.status === 'done'));
const pagedDone  = computed(() => {
  const s = (tablePage.value - 1) * tablePageSize;
  return doneModels.value.slice(s, s + tablePageSize);
});
const isDL = computed(() => selected.value?.model_type !== 'RF');

const modelName = (m) => m.file_path ? m.file_path.split(/[/\\]/).pop() : `${m.model_type}_#${m.id}`;
const fmtE = (v) => v != null ? Number(v).toExponential(4) : '--';

const metricCards = computed(() => {
  if (!selected.value?.metrics) return [];
  const m = selected.value.metrics;
  const cards = [
    { label:'Train Loss (原始空间)', value: fmtE(m.final_train_loss), hint:'反变换后 MAE', color:'#60a5fa', bg:'rgba(59,130,246,0.07)', border:'rgba(59,130,246,0.2)' },
    { label:'Test Loss (原始空间)',  value: fmtE(m.final_test_loss),  hint:'反变换后 MAE', color:'#f472b6', bg:'rgba(236,72,153,0.07)', border:'rgba(236,72,153,0.2)' },
    { label:'输入维度',   value: m.input_dim ?? '--',       hint:'特征数',    color:'#34d399', bg:'rgba(16,185,129,0.07)', border:'rgba(16,185,129,0.2)' },
    { label:'输出维度',   value: m.output_dim ?? '--',      hint:'PCA 主成分数', color:'#fbbf24', bg:'rgba(245,158,11,0.07)', border:'rgba(245,158,11,0.2)' },
  ];
  if (m.final_test_loss_pca != null) {
    cards.push({ label:'Test Loss (PCA空间)', value: fmtE(m.final_test_loss_pca), hint:'主成分 MAE（训练目标）', color:'#a78bfa', bg:'rgba(139,92,246,0.07)', border:'rgba(139,92,246,0.2)' });
  }
  return cards;
});

const genRatio = computed(() => {
  const m = selected.value?.metrics;
  if (!m || !m.final_train_loss) return 0;
  return m.final_test_loss / m.final_train_loss;
});

const hasLossHistory = computed(() => {
  const h = selected.value?.metrics?.loss_history;
  return h && h.epochs?.length > 0;
});

const lossChartOption = computed(() => {
  const h = selected.value?.metrics?.loss_history;
  if (!h) return {};
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(2,8,23,0.9)', borderColor: 'rgba(51,65,85,0.5)', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    legend: { data: ['Train Loss', 'Test Loss'], textStyle: { color: '#94a3b8', fontSize: 11 }, top: 0 },
    grid: { top: 36, left: 60, right: 20, bottom: 36 },
    xAxis: {
      type: 'category', data: h.epochs,
      name: 'Epoch', nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#64748b', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)' } },
    },
    yAxis: {
      type: 'value', name: 'Loss',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#64748b', fontSize: 10, formatter: v => v.toExponential(1) },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)' } },
    },
    series: [
      { name: 'Train Loss', type: 'line', data: h.train, smooth: true,
        lineStyle: { color: '#60a5fa', width: 2 }, symbol: 'none',
        areaStyle: { color: 'rgba(96,165,250,0.06)' } },
      { name: 'Test Loss',  type: 'line', data: h.test,  smooth: true,
        lineStyle: { color: '#f472b6', width: 2 }, symbol: 'none',
        areaStyle: { color: 'rgba(244,114,182,0.06)' } },
    ],
  };
});

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
    const aid = parseInt(localStorage.getItem('active_model_id') || '0');
    const found = doneModels.value.find(m => m.id === aid) || doneModels.value[0];
    if (found) selected.value = found;
  } catch (e) {
    ElMessage.error(`加载失败：${e.message}`);
  } finally {
    loading.value = false;
  }
};

const select = (row) => { if (row) selected.value = row; };

onMounted(fetchModels);
</script>

<style scoped>
.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.375rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  background: rgba(2,8,23,0.4);
  border: 1px solid rgba(51,65,85,0.3);
}
.config-row span:first-child { color: #64748b; }
.config-row span:last-child  { color: #e2e8f0; font-family: monospace; font-weight: 600; }
:deep(.el-table__row.selected-row td) { background: rgba(59,130,246,0.1) !important; }
:deep(.el-table__body tr:hover > td) { background: rgba(59,130,246,0.06) !important; }
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) { background-color: #3b82f6; }
:deep(.el-pagination.is-background .el-pager li) { background-color: rgba(10,18,36,0.9); color: #64748b; }
:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) { background-color: rgba(10,18,36,0.9); color: #64748b; }
</style>
