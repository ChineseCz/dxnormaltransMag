<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- 页面标题 -->
    <div class="px-6 pt-6 pb-4">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="flex items-center gap-3">
            <div class="rounded-xl flex items-center justify-center flex-shrink-0"
                 style="width:36px;height:36px;background:linear-gradient(135deg,#3b82f6,#2563eb); box-shadow:0 0 20px rgba(59,130,246,0.4);">
              <el-icon size="20" style="color:#fff;"><DataLine /></el-icon>
            </div>
            <h1 class="text-2xl font-extrabold tracking-tight"
                style="background:linear-gradient(90deg,#60a5fa,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              结果可视化
            </h1>
          </div>
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">物理场预测结果的多维度图表展示与数据导出</p>
        </div>
        <div v-if="result" class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
             style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399;">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span>
          {{ result.modelType }} · {{ result.timestamp }}
        </div>
      </div>
    </div>

    <!-- 主体 -->
    <div class="px-6 pb-6 space-y-5">
      <!-- 统计指标卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="result">
        <div v-for="(s, idx) in statCards" :key="idx" class="stat-card" :style="s.style">
          <div class="text-[10px] font-bold uppercase tracking-widest mb-1" :style="`color:${s.labelColor}`">{{ s.label }}</div>
          <div class="text-xl font-extrabold font-mono" :style="`color:${s.valueColor}`">{{ s.value }}</div>
          <div class="text-[10px] mt-1" style="color:#64748b;">{{ s.desc }}</div>
        </div>
      </div>

      <!-- 图表区 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <!-- 物理场分布曲线 -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-md flex items-center justify-center" style="background:rgba(59,130,246,0.15);">
                <el-icon size="13" style="color:#60a5fa;"><TrendCharts /></el-icon>
              </div>
              <span class="text-white font-bold text-sm">物理场空间分布</span>
            </div>
            <el-radio-group v-model="chartMode" size="small">
              <el-radio-button value="line">曲线</el-radio-button>
              <el-radio-button value="bar">柱状</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-body">
            <v-chart v-if="result" :option="fieldDistOption" autoresize class="h-full w-full" />
            <div v-else class="empty-state"><el-icon size="40" style="color:#334155;"><PictureFilled /></el-icon><p class="text-slate-600 text-xs mt-2">暂无预测结果</p></div>
          </div>
        </div>

        <!-- 场值分布直方图 -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-md flex items-center justify-center" style="background:rgba(168,85,247,0.15);">
                <el-icon size="13" style="color:#c084fc;"><Histogram /></el-icon>
              </div>
              <span class="text-white font-bold text-sm">场值频率分布</span>
            </div>
          </div>
          <div class="chart-body">
            <v-chart v-if="result" :option="histogramOption" autoresize class="h-full w-full" />
            <div v-else class="empty-state"><el-icon size="40" style="color:#334155;"><PictureFilled /></el-icon><p class="text-slate-600 text-xs mt-2">暂无预测结果</p></div>
          </div>
        </div>
      </div>

      <!-- 空间热力散点图 -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-md flex items-center justify-center" style="background:rgba(16,185,129,0.15);">
              <el-icon size="13" style="color:#34d399;"><Place /></el-icon>
            </div>
            <span class="text-white font-bold text-sm">空间场点热力图</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-500 text-[11px]">场点数:</span>
            <span class="text-green-400 text-xs font-mono font-bold">{{ fieldValues.length }}</span>
          </div>
        </div>
        <div class="h-[400px] p-4">
          <v-chart v-if="result && hasCoordinates" :option="heatmapOption" autoresize class="h-full w-full" />
          <div v-else-if="result" class="empty-state h-full">
            <el-icon size="40" style="color:#334155;"><Place /></el-icon>
            <p class="text-slate-600 text-xs mt-2">无坐标数据，无法绘制空间分布</p>
          </div>
          <div v-else class="empty-state h-full">
            <el-icon size="40" style="color:#334155;"><PictureFilled /></el-icon>
            <p class="text-slate-600 text-xs mt-2">暂无预测结果</p>
          </div>
        </div>
      </div>

      <!-- 数据表格 -->
      <div class="chart-card" v-if="result">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-md flex items-center justify-center" style="background:rgba(245,158,11,0.15);">
              <el-icon size="13" style="color:#fbbf24;"><Grid /></el-icon>
            </div>
            <span class="text-white font-bold text-sm">场点数值明细</span>
          </div>
          <div class="flex items-center gap-3">
            <el-input v-model="tableSearch" size="small" placeholder="搜索场点..." clearable style="width:160px;" prefix-icon="Search" />
            <el-button size="small" text style="color:#64748b;" @click="exportCSV">
              <el-icon class="mr-1"><Download /></el-icon>导出 CSV
            </el-button>
          </div>
        </div>
        <div class="p-4">
          <el-table :data="pagedTableData" max-height="360" class="result-table"
                    :header-cell-style="{ background:'#0f172a', color:'#94a3b8', borderColor:'rgba(51,65,85,0.4)' }"
                    :cell-style="{ background:'transparent', color:'#e2e8f0', borderColor:'rgba(51,65,85,0.3)' }">
            <el-table-column label="#" width="70" align="center">
              <template #default="{ $index }"><span class="text-slate-500 font-mono text-xs">{{ (currentPage - 1) * pageSize + $index + 1 }}</span></template>
            </el-table-column>
            <el-table-column v-if="hasCoordinates" label="X" width="120" align="center">
              <template #default="{ row }"><span class="font-mono text-blue-400 text-xs">{{ row.x?.toFixed(4) }}</span></template>
            </el-table-column>
            <el-table-column v-if="hasCoordinates" label="Y" width="120" align="center">
              <template #default="{ row }"><span class="font-mono text-purple-400 text-xs">{{ row.y?.toFixed(4) }}</span></template>
            </el-table-column>
            <el-table-column v-if="hasCoordinates && has3D" label="Z" width="120" align="center">
              <template #default="{ row }"><span class="font-mono text-green-400 text-xs">{{ row.z?.toFixed(4) }}</span></template>
            </el-table-column>
            <el-table-column :label="fieldLabel" min-width="180">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <div class="h-1.5 rounded-full" :style="`width:${row.barWidth}%; background:${row.barColor};`"></div>
                  <span class="font-mono text-xs" :style="`color:${row.barColor};`">{{ row.value.toExponential(4) }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="flex justify-center mt-4" v-if="filteredTableData.length > pageSize">
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize"
                           :total="filteredTableData.length" layout="prev, pager, next" small background />
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div v-if="!result" class="flex flex-col items-center justify-center py-24">
        <el-icon size="56" style="color:#1e293b;"><PictureFilled /></el-icon>
        <p class="text-slate-600 text-sm mt-4">暂无预测结果</p>
        <p class="text-slate-700 text-xs mt-1">请先前往「预测配置」页面完成一次预测</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import {
  TrendCharts, Histogram, Place, PictureFilled, Grid, Download, DataLine,
} from '@element-plus/icons-vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart, ScatterChart, HeatmapChart } from 'echarts/charts';
import {
  GridComponent, TooltipComponent, LegendComponent,
  VisualMapComponent, DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

use([
  CanvasRenderer, LineChart, BarChart, ScatterChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent,
  VisualMapComponent, DataZoomComponent,
]);

const { predictionResult: result, activeDataset: dataset } = usePredictionStore();

const chartMode = ref('line');
const tableSearch = ref('');
const currentPage = ref(1);
const pageSize = 50;

// ──── 核心数据提取 ────
const fieldValues = computed(() => result.value?.fieldValues || []);
const coordinates = computed(() => result.value?.coordinates || []);
const hasCoordinates = computed(() => coordinates.value.length > 0);
const has3D = computed(() => coordinates.value.length > 0 && coordinates.value[0]?.length >= 3);

const fieldUnit = computed(() => {
  const ft = dataset.value?.fieldType;
  const MAP = { magnetic: 'T', temperature: '°C', stress: 'Pa', electric: 'V/m', flow: 'm/s' };
  return MAP[ft] || '';
});
const fieldName = computed(() => {
  const ft = dataset.value?.fieldType;
  const MAP = { magnetic: '磁通密度 B', temperature: '温度 T', stress: '应力 σ', electric: '电场 E', flow: '流速 v' };
  return MAP[ft] || '物理场';
});
const fieldLabel = computed(() => fieldUnit.value ? `${fieldName.value} (${fieldUnit.value})` : fieldName.value);

// ──── 统计 ────
const stats = computed(() => {
  if (result.value?.stats) return result.value.stats;
  const fv = fieldValues.value;
  if (!fv.length) return { min: 0, max: 0, mean: 0, std: 0 };
  const min = Math.min(...fv);
  const max = Math.max(...fv);
  const mean = fv.reduce((a, b) => a + b, 0) / fv.length;
  const std = Math.sqrt(fv.reduce((s, v) => s + (v - mean) ** 2, 0) / fv.length);
  return { min, max, mean, std };
});

const statCards = computed(() => [
  { label: '最小值', value: stats.value.min?.toExponential(3), desc: `Min ${fieldUnit.value}`, labelColor: '#38bdf8', valueColor: '#7dd3fc', style: 'background:rgba(14,165,233,0.06); border:1px solid rgba(14,165,233,0.15);' },
  { label: '最大值', value: stats.value.max?.toExponential(3), desc: `Max ${fieldUnit.value}`, labelColor: '#f472b6', valueColor: '#f9a8d4', style: 'background:rgba(236,72,153,0.06); border:1px solid rgba(236,72,153,0.15);' },
  { label: '均值', value: stats.value.mean?.toExponential(3), desc: `Mean ${fieldUnit.value}`, labelColor: '#a78bfa', valueColor: '#c4b5fd', style: 'background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.15);' },
  { label: '标准差', value: stats.value.std?.toExponential(3), desc: 'Standard Deviation', labelColor: '#34d399', valueColor: '#6ee7b7', style: 'background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);' },
]);

// ──── 场分布图 ────
const fieldDistOption = computed(() => {
  const fv = fieldValues.value;
  const indices = fv.map((_, i) => i);
  const isLine = chartMode.value === 'line';
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(59,130,246,0.3)',
      textStyle: { color: '#e2e8f0', fontSize: 11 },
      formatter: (params) => {
        const p = params[0];
        return `<b>场点 #${p.dataIndex}</b><br/>${fieldName.value}: <b>${Number(p.value).toExponential(4)}</b> ${fieldUnit.value}`;
      },
    },
    grid: { top: 40, left: 60, right: 30, bottom: 60, containLabel: false },
    xAxis: {
      type: 'category', data: indices, name: '场点索引',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#475569', fontSize: 10, interval: Math.floor(fv.length / 10) },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', name: fieldLabel.value,
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#475569', fontSize: 10, formatter: (v) => v.toExponential(1) },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)', type: 'dashed' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, height: 20, bottom: 8,
        borderColor: 'transparent', backgroundColor: 'rgba(51,65,85,0.2)',
        fillerColor: 'rgba(59,130,246,0.15)', handleStyle: { color: '#3b82f6' },
        textStyle: { color: '#64748b', fontSize: 10 },
      },
    ],
    series: [{
      type: isLine ? 'line' : 'bar',
      data: fv,
      smooth: isLine ? 0.3 : false,
      symbol: 'none',
      lineStyle: { width: 1.5, color: '#3b82f6' },
      areaStyle: isLine ? {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59,130,246,0.25)' },
            { offset: 1, color: 'rgba(59,130,246,0)' },
          ],
        },
      } : undefined,
      itemStyle: { color: '#3b82f6' },
    }],
  };
});

// ──── 直方图 ────
const histogramOption = computed(() => {
  const fv = fieldValues.value;
  if (!fv.length) return {};
  const min = Math.min(...fv), max = Math.max(...fv);
  const binCount = 30;
  const binWidth = (max - min) / binCount || 1;
  const bins = Array.from({ length: binCount }, () => 0);
  fv.forEach(v => {
    const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1);
    bins[idx]++;
  });
  const labels = bins.map((_, i) => (min + i * binWidth).toExponential(1));

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(168,85,247,0.3)',
      textStyle: { color: '#e2e8f0', fontSize: 11 },
    },
    grid: { top: 30, left: 60, right: 20, bottom: 40, containLabel: false },
    xAxis: {
      type: 'category', data: labels,
      axisLabel: { color: '#475569', fontSize: 9, rotate: 30 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value', name: '频次',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#475569', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.3)', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: bins,
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#a78bfa' },
            { offset: 1, color: '#6d28d9' },
          ],
        },
        borderRadius: [3, 3, 0, 0],
      },
      barWidth: '60%',
    }],
  };
});

// ──── 空间热力图（2D 散点色彩映射） ────
const heatmapOption = computed(() => {
  const coords = coordinates.value;
  const fv = fieldValues.value;
  if (!coords.length) return {};

  const data = coords.map((c, i) => [...c.slice(0, 2), fv[i] ?? 0]);
  const min = Math.min(...fv), max = Math.max(...fv);

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(16,185,129,0.3)',
      textStyle: { color: '#e2e8f0', fontSize: 11 },
      formatter: (p) => {
        const [x, y, v] = p.value;
        return `X: ${x.toFixed(4)}<br/>Y: ${y.toFixed(4)}<br/>${fieldName.value}: <b>${v.toExponential(4)}</b> ${fieldUnit.value}`;
      },
    },
    grid: { top: 30, left: 50, right: 80, bottom: 40 },
    xAxis: {
      type: 'value', name: 'X',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#475569', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.2)' } },
    },
    yAxis: {
      type: 'value', name: 'Y',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#475569', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.2)' } },
    },
    visualMap: {
      min, max, calculable: true, orient: 'vertical', right: 10, top: 'center',
      inRange: { color: ['#3b82f6', '#22d3ee', '#34d399', '#fbbf24', '#ef4444'] },
      textStyle: { color: '#94a3b8', fontSize: 10 },
      formatter: (v) => v.toExponential(1),
    },
    series: [{
      type: 'scatter',
      data,
      symbolSize: 5,
      itemStyle: { borderWidth: 0 },
    }],
  };
});

// ──── 表格数据 ────
const allTableData = computed(() => {
  const fv = fieldValues.value;
  const coords = coordinates.value;
  const min = Math.min(...fv), max = Math.max(...fv);
  const range = max - min || 1;

  return fv.map((v, i) => {
    const ratio = (v - min) / range;
    const barColor = ratio > 0.7 ? '#ef4444' : ratio > 0.4 ? '#fbbf24' : '#3b82f6';
    return {
      index: i,
      x: coords[i]?.[0] ?? null,
      y: coords[i]?.[1] ?? null,
      z: coords[i]?.[2] ?? null,
      value: v,
      barWidth: Math.max(5, ratio * 100),
      barColor,
    };
  });
});

const filteredTableData = computed(() => {
  if (!tableSearch.value) return allTableData.value;
  const q = tableSearch.value.toLowerCase();
  return allTableData.value.filter(r =>
    String(r.index).includes(q) || r.value.toExponential(4).includes(q)
  );
});

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredTableData.value.slice(start, start + pageSize);
});

watch(() => result.value, () => { currentPage.value = 1; });

// ──── 导出 CSV ────
function exportCSV() {
  const fv = fieldValues.value;
  const coords = coordinates.value;
  let csv = hasCoordinates.value
    ? (has3D.value ? 'Index,X,Y,Z,Value\n' : 'Index,X,Y,Value\n')
    : 'Index,Value\n';
  fv.forEach((v, i) => {
    const row = [i];
    if (hasCoordinates.value) {
      row.push(coords[i]?.[0] ?? '', coords[i]?.[1] ?? '');
      if (has3D.value) row.push(coords[i]?.[2] ?? '');
    }
    row.push(v);
    csv += row.join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `prediction_${result.value?.id || 'result'}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.stat-card {
  padding: 14px 16px;
  border-radius: 12px;
}
.chart-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  border-bottom: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.4);
}
.chart-body {
  height: 340px;
  padding: 12px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 表格暗色 */
.result-table {
  --el-table-border-color: rgba(51,65,85,0.3);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: #0f172a;
  --el-table-header-text-color: #94a3b8;
  --el-table-text-color: #e2e8f0;
}
:deep(.el-table__row:hover > td) {
  background-color: rgba(59,130,246,0.06) !important;
}

/* Radio group dark mode */
:deep(.el-radio-button__inner) {
  background: rgba(15,23,42,0.6) !important;
  border-color: rgba(51,65,85,0.4) !important;
  color: #94a3b8 !important;
  font-size: 11px;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(59,130,246,0.2) !important;
  border-color: rgba(59,130,246,0.4) !important;
  color: #60a5fa !important;
  box-shadow: none !important;
}
</style>


