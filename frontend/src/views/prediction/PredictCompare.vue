<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- 页面标题 -->
    <div class="px-6 pt-6 pb-4">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#8b5cf6,#6d28d9); box-shadow:0 0 20px rgba(139,92,246,0.4);">
            <el-icon size="20" style="color:#fff;"><Switch /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#c084fc,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            多次对比
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">选取两条预测记录，对比电磁场分布差异与误差指标</p>
      </div>
    </div>

    <div class="px-6 pb-6 space-y-5">
      <!-- ═══════ 选择对比记录 ═══════ -->
      <div class="compare-card">
        <!-- ...existing card-header and selection content... -->
        <div class="card-header">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center"
                 style="background:rgba(245,158,11,0.15);">
              <el-icon size="15" style="color:#fbbf24;"><Switch /></el-icon>
            </div>
            <span class="text-white font-bold text-sm">选择对比记录</span>
          </div>
          <span class="text-slate-500 text-[11px]">选取两条预测记录进行场分布对比分析</span>
        </div>
        <div class="p-5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 记录 A -->
            <div class="p-4 rounded-xl" style="background:rgba(59,130,246,0.05); border:1px solid rgba(59,130,246,0.2);">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
                      style="background:rgba(59,130,246,0.2); color:#60a5fa;">A</span>
                <span class="text-blue-400 text-xs font-bold">基准记录</span>
              </div>
              <el-select v-model="selectedA" placeholder="选择预测记录 A..." filterable clearable class="w-full" size="large">
                <el-option v-for="r in history" :key="r.id" :label="formatLabel(r)" :value="r.id">
                  <div class="flex items-center justify-between w-full">
                    <span class="text-slate-200 text-xs">{{ r.timestamp }}</span>
                    <el-tag size="small" effect="plain" round>{{ r.modelType }}</el-tag>
                  </div>
                </el-option>
              </el-select>
            </div>
            <!-- 记录 B -->
            <div class="p-4 rounded-xl" style="background:rgba(168,85,247,0.05); border:1px solid rgba(168,85,247,0.2);">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
                      style="background:rgba(168,85,247,0.2); color:#c084fc;">B</span>
                <span class="text-purple-400 text-xs font-bold">对比记录</span>
              </div>
              <el-select v-model="selectedB" placeholder="选择预测记录 B..." filterable clearable class="w-full" size="large">
                <el-option v-for="r in history" :key="r.id" :label="formatLabel(r)" :value="r.id">
                  <div class="flex items-center justify-between w-full">
                    <span class="text-slate-200 text-xs">{{ r.timestamp }}</span>
                    <el-tag size="small" effect="plain" round>{{ r.modelType }}</el-tag>
                  </div>
                </el-option>
              </el-select>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ 对比图表 (当两条都选中时) ═══════ -->
      <template v-if="canCompare">
        <!-- 输入参数差异 -->
        <div class="compare-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <el-icon size="14" style="color:#818cf8;"><List /></el-icon>
              <span class="text-white font-bold text-sm">输入参数对比</span>
            </div>
          </div>
          <div class="p-5">
            <el-table :data="inputCompareData" class="compare-table"
                      :header-cell-style="{ background:'#0f172a', color:'#94a3b8', borderColor:'rgba(51,65,85,0.4)' }"
                      :cell-style="{ background:'transparent', color:'#e2e8f0', borderColor:'rgba(51,65,85,0.3)' }">
              <el-table-column label="参数名称" prop="name" min-width="150">
                <template #default="{ row }"><span class="text-slate-300 text-xs font-semibold">{{ row.name }}</span></template>
              </el-table-column>
              <el-table-column label="记录 A" width="160" align="center">
                <template #default="{ row }"><span class="text-blue-400 font-mono text-xs">{{ row.valueA }}</span></template>
              </el-table-column>
              <el-table-column label="记录 B" width="160" align="center">
                <template #default="{ row }"><span class="text-purple-400 font-mono text-xs">{{ row.valueB }}</span></template>
              </el-table-column>
              <el-table-column label="差异" width="160" align="center">
                <template #default="{ row }">
                  <span :class="row.diff === 0 ? 'text-slate-500' : 'text-amber-400'" class="font-mono text-xs">
                    {{ row.diff === 0 ? '—' : row.diff > 0 ? `+${row.diff.toFixed(4)}` : row.diff.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 场值叠加曲线 -->
        <div class="compare-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <el-icon size="14" style="color:#60a5fa;"><TrendCharts /></el-icon>
              <span class="text-white font-bold text-sm">电磁场分布叠加对比</span>
            </div>
          </div>
          <div class="h-[380px] p-4">
            <v-chart :option="overlayOption" autoresize class="h-full w-full" />
          </div>
        </div>

        <!-- 差值分布 + 误差指标 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div class="compare-card">
            <div class="card-header">
              <div class="flex items-center gap-2">
                <el-icon size="14" style="color:#f472b6;"><DataLine /></el-icon>
                <span class="text-white font-bold text-sm">差值分布 (A − B)</span>
              </div>
            </div>
            <div class="h-[320px] p-4">
              <v-chart :option="diffOption" autoresize class="h-full w-full" />
            </div>
          </div>
          <div class="compare-card">
            <div class="card-header">
              <div class="flex items-center gap-2">
                <el-icon size="14" style="color:#34d399;"><Histogram /></el-icon>
                <span class="text-white font-bold text-sm">对比统计指标</span>
              </div>
            </div>
            <div class="p-5 space-y-4">
              <div v-for="(metric, idx) in diffMetrics" :key="idx"
                   class="flex items-center justify-between p-3 rounded-lg" :style="metric.bgStyle">
                <div>
                  <div class="text-[10px] font-bold uppercase tracking-widest" :style="`color:${metric.color}`">{{ metric.label }}</div>
                  <div class="text-[11px] text-slate-500 mt-0.5">{{ metric.desc }}</div>
                </div>
                <div class="text-lg font-extrabold font-mono" :style="`color:${metric.color}`">{{ metric.value }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 无选择时提示 -->
      <div v-else class="flex flex-col items-center justify-center py-20">
        <el-icon size="56" style="color:#1e293b;"><Switch /></el-icon>
        <p class="text-slate-600 text-sm mt-4">请从上方选择两条预测记录进行对比分析</p>
        <p class="text-slate-700 text-xs mt-1" v-if="history.length < 2">
          当前历史记录不足 2 条，请先完成更多预测
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import {
  Switch, List, TrendCharts, DataLine, Histogram,
} from '@element-plus/icons-vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import {
  GridComponent, TooltipComponent, LegendComponent, DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent]);

const { predictionHistory: history } = usePredictionStore();

const selectedA = ref('');
const selectedB = ref('');

const recordA = computed(() => history.value.find(r => r.id === selectedA.value));
const recordB = computed(() => history.value.find(r => r.id === selectedB.value));
const canCompare = computed(() => recordA.value && recordB.value);

function formatLabel(r) {
  return `${r.timestamp} | ${r.modelType} | ${r.datasetName || ''}`;
}

// ──── 输入参数对比表 ────
const inputCompareData = computed(() => {
  if (!canCompare.value) return [];
  const keysA = Object.keys(recordA.value.inputs || {});
  const keysB = Object.keys(recordB.value.inputs || {});
  const allKeys = [...new Set([...keysA, ...keysB])];
  return allKeys.map(k => {
    const a = recordA.value.inputs?.[k] ?? 0;
    const b = recordB.value.inputs?.[k] ?? 0;
    return { name: k, valueA: a, valueB: b, diff: a - b };
  });
});

// ──── 叠加曲线 ────
const overlayOption = computed(() => {
  if (!canCompare.value) return {};
  const fvA = recordA.value.fieldValues || [];
  const fvB = recordB.value.fieldValues || [];
  const len = Math.max(fvA.length, fvB.length);
  const indices = Array.from({ length: len }, (_, i) => i);

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.95)', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    legend: {
      data: ['记录 A', '记录 B'],
      textStyle: { color: '#94a3b8', fontSize: 11 },
      top: 6,
    },
    grid: { top: 40, left: 60, right: 30, bottom: 60 },
    xAxis: {
      type: 'category', data: indices, name: '场点索引',
      axisLabel: { color: '#475569', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#475569', fontSize: 10, formatter: v => v.toExponential(1) },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)', type: 'dashed' } },
    },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 18, bottom: 6, borderColor: 'transparent',
        backgroundColor: 'rgba(51,65,85,0.2)', fillerColor: 'rgba(59,130,246,0.1)',
        textStyle: { color: '#64748b', fontSize: 9 } },
    ],
    series: [
      { name: '记录 A', type: 'line', data: fvA, smooth: 0.3, symbol: 'none',
        lineStyle: { width: 2, color: '#3b82f6' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.15)' }, { offset: 1, color: 'rgba(59,130,246,0)' }] } },
      },
      { name: '记录 B', type: 'line', data: fvB, smooth: 0.3, symbol: 'none',
        lineStyle: { width: 2, color: '#c084fc', type: 'dashed' },
      },
    ],
  };
});

// ──── 差值分布 ────
const diffValues = computed(() => {
  if (!canCompare.value) return [];
  const a = recordA.value.fieldValues || [];
  const b = recordB.value.fieldValues || [];
  const len = Math.min(a.length, b.length);
  return Array.from({ length: len }, (_, i) => a[i] - b[i]);
});

const diffOption = computed(() => {
  const dv = diffValues.value;
  if (!dv.length) return {};
  const min = Math.min(...dv), max = Math.max(...dv);
  const binCount = 30;
  const binWidth = (max - min) / binCount || 1;
  const bins = Array.from({ length: binCount }, () => 0);
  dv.forEach(v => {
    const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1);
    bins[idx]++;
  });
  const labels = bins.map((_, i) => (min + i * binWidth).toExponential(1));

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.95)', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    grid: { top: 20, left: 60, right: 20, bottom: 40 },
    xAxis: {
      type: 'category', data: labels, name: '差值',
      axisLabel: { color: '#475569', fontSize: 9, rotate: 30 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value', name: '频次',
      axisLabel: { color: '#475569', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)', type: 'dashed' } },
    },
    series: [{
      type: 'bar', data: bins,
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#f472b6' }, { offset: 1, color: '#be185d' }] },
        borderRadius: [3, 3, 0, 0],
      },
      barWidth: '60%',
    }],
  };
});

// ──── 误差指标 ────
const diffMetrics = computed(() => {
  const dv = diffValues.value;
  if (!dv.length) return [];

  const n = dv.length;
  const mae = dv.reduce((s, v) => s + Math.abs(v), 0) / n;
  const mse = dv.reduce((s, v) => s + v * v, 0) / n;
  const rmse = Math.sqrt(mse);
  const maxDiff = Math.max(...dv.map(Math.abs));

  // R² 以 A 为参考
  const a = recordA.value.fieldValues || [];
  const meanA = a.reduce((s, v) => s + v, 0) / a.length;
  const ssRes = dv.reduce((s, v) => s + v * v, 0);
  const ssTot = a.reduce((s, v) => s + (v - meanA) ** 2, 0);
  const r2 = ssTot > 0 ? (1 - ssRes / ssTot) : 0;

  return [
    { label: 'MAE', desc: 'Mean Absolute Error', value: mae.toExponential(3),
      color: '#38bdf8', bgStyle: 'background:rgba(14,165,233,0.06); border:1px solid rgba(14,165,233,0.15);' },
    { label: 'RMSE', desc: 'Root Mean Square Error', value: rmse.toExponential(3),
      color: '#f472b6', bgStyle: 'background:rgba(236,72,153,0.06); border:1px solid rgba(236,72,153,0.15);' },
    { label: 'Max|Δ|', desc: 'Maximum Absolute Difference', value: maxDiff.toExponential(3),
      color: '#fbbf24', bgStyle: 'background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15);' },
    { label: 'R²', desc: 'Coefficient of Determination', value: r2.toFixed(6),
      color: '#34d399', bgStyle: 'background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);' },
  ];
});
</script>

<style scoped>
.compare-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.4);
}
.compare-table {
  --el-table-border-color: rgba(51,65,85,0.3);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}
:deep(.el-table__row:hover > td) {
  background-color: rgba(59,130,246,0.06) !important;
}
</style>


