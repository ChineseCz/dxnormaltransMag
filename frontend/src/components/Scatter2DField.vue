<template>
  <div ref="containerEl" class="relative w-full h-full select-none">
    <div ref="chartEl" class="w-full h-full" />

    <!-- 操作提示 -->
    <div style="position:absolute;left:12px;top:12px;pointer-events:none;" class="space-y-1">
      <div class="bg-black/35 rounded px-2.5 py-0.5 text-[9px] text-slate-500">
        左键框选 &nbsp;·&nbsp; 滚轮缩放 &nbsp;·&nbsp; 双击复位
      </div>
    </div>

    <!-- 无数据占位 -->
    <div v-if="!hasData"
         class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-slate-600">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span class="text-xs">暂无 r-z 场点数据</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  points: { type: Array, default: () => [] },  // [{r, z, value}]
  unit:   { type: String, default: 'T' },
  label:  { type: String, default: 'B' },
  rLabel: { type: String, default: 'r / mm' },
  zLabel: { type: String, default: 'z / mm' },
});

const containerEl = ref(null);
const chartEl     = ref(null);
const hasData     = computed(() => props.points.length > 0);

let chart = null;
let ro    = null;

/** Jet 色带 */
const JET_COLORS = [
  '#00007f','#0000ff','#007fff','#00ffff',
  '#7fff7f','#ffff00','#ff7f00','#ff0000','#7f0000',
];

const fmt = (v) =>
  v == null || isNaN(v) ? '--'
  : (Math.abs(v) < 0.001 || Math.abs(v) >= 1000) ? v.toExponential(3)
  : v.toFixed(4);

function buildOption(pts) {
  if (!pts || pts.length === 0) return {};

  let vMin = Infinity, vMax = -Infinity;
  let rMin = Infinity, rMax = -Infinity;
  let zMin = Infinity, zMax = -Infinity;

  const data = pts.map(p => {
    if (p.value < vMin) vMin = p.value;
    if (p.value > vMax) vMax = p.value;
    if (p.r < rMin) rMin = p.r;
    if (p.r > rMax) rMax = p.r;
    if (p.z < zMin) zMin = p.z;
    if (p.z > zMax) zMax = p.z;
    return [p.r, p.z, p.value];
  });

  if (vMin === vMax) { vMin -= 1e-6; vMax += 1e-6; }

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10,20,40,0.85)',
      borderColor: 'rgba(96,165,250,0.3)',
      textStyle: { color: '#e2e8f0', fontSize: 12, fontFamily: 'Consolas, monospace' },
      formatter(params) {
        const d = params.data;
        return `<b style="color:#fbbf24">${props.label}</b><br/>`
             + `r: <b>${d[0].toFixed(2)}</b> mm<br/>`
             + `z: <b>${d[1].toFixed(2)}</b> mm<br/>`
             + `${props.label}: <b style="color:#34d399">${fmt(d[2])}</b> ${props.unit}`;
      },
    },
    toolbox: {
      show: true,
      right: 80,
      top: 8,
      iconStyle: { borderColor: '#475569' },
      emphasis: { iconStyle: { borderColor: '#60a5fa' } },
      feature: {
        dataZoom: { show: true, title: { zoom: '框选缩放', back: '还原' } },
        restore:  { show: true, title: '还原' },
        saveAsImage: { show: true, title: '保存图片', backgroundColor: '#060d1a' },
      },
    },
    visualMap: {
      show: true,
      min: vMin,
      max: vMax,
      calculable: true,
      dimension: 2,
      inRange: { color: JET_COLORS },
      text: [fmt(vMax), fmt(vMin)],
      textStyle: { color: '#94a3b8', fontSize: 10, fontFamily: 'Consolas, monospace' },
      right: 16,
      top: 'center',
      itemWidth: 14,
      itemHeight: 180,
      textGap: 5,
    },
    grid: {
      top: 40, bottom: 56, left: 72, right: 100,
      containLabel: false,
    },
    xAxis: {
      type: 'value',
      name: props.rLabel,
      nameLocation: 'middle',
      nameGap: 34,
      nameTextStyle: { color: '#60a5fa', fontSize: 12, fontWeight: 'bold' },
      axisLine:  { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.4)' } },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: 'Consolas, monospace' },
      min: Math.floor(rMin / 100) * 100,
      max: Math.ceil(rMax  / 100) * 100,
    },
    yAxis: {
      type: 'value',
      name: props.zLabel,
      nameLocation: 'middle',
      nameGap: 50,
      nameTextStyle: { color: '#60a5fa', fontSize: 12, fontWeight: 'bold' },
      axisLine:  { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(51,65,85,0.4)' } },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: 'Consolas, monospace' },
      min: Math.floor(zMin / 100) * 100,
      max: Math.ceil(zMax  / 100) * 100,
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, bottom: 4, height: 18,
        borderColor: '#334155', fillerColor: 'rgba(59,130,246,0.15)',
        textStyle: { color: '#64748b', fontSize: 9 } },
    ],
    series: [{
      type: 'scatter',
      data,
      symbolSize: 3.5,
      itemStyle: { opacity: 0.85, borderWidth: 0 },
      emphasis: {
        scale: true,
        itemStyle: { opacity: 1, borderColor: '#fff', borderWidth: 1 },
      },
      large: true,
      largeThreshold: 2000,
    }],
  };
}

function updateChart() {
  if (!chart || !hasData.value) return;
  chart.setOption(buildOption(props.points), { notMerge: true });
}

onMounted(async () => {
  await nextTick();
  if (!chartEl.value) return;
  chart = echarts.init(chartEl.value, null, { renderer: 'canvas' });
  updateChart();
  ro = new ResizeObserver(() => chart && chart.resize());
  ro.observe(containerEl.value);
});

onBeforeUnmount(() => {
  if (ro)    { ro.disconnect(); ro = null; }
  if (chart) { chart.dispose();  chart = null; }
});

watch(() => props.points, () => updateChart(), { deep: false });
</script>

