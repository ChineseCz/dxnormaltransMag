<template>
  <div ref="containerEl" class="relative w-full h-full select-none">
    <!-- ECharts GL 容器 -->
    <div ref="chartEl" class="w-full h-full" />

    <!-- Info overlay -->
    <div style="position:absolute; left:12px; top:12px; pointer-events:none;" class="space-y-1">
      <div class="bg-black/55 backdrop-blur-sm rounded px-2.5 py-1 text-[10px] font-mono text-slate-300">
<!--        {{ nPts }} 场点 &nbsp;·&nbsp; ECharts GL 硬件渲染-->
      </div>
      <div class="bg-black/35 rounded px-2.5 py-0.5 text-[9px] text-slate-500">
        左键旋转 &nbsp;·&nbsp; 右键平移 &nbsp;·&nbsp; 滚轮缩放
      </div>
    </div>

    <!-- No-data placeholder -->
    <div v-if="!hasData"
         class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-slate-600">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
      <span class="text-xs">暂无三维场点数据</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';
import 'echarts-gl';

const props = defineProps({
  points:    { type: Array,  default: () => [] },
  unit:      { type: String, default: 'T' },
  label:     { type: String, default: 'B' },
  boxWidth:  { type: Number, default: 80 },
  boxHeight: { type: Number, default: 40 },
  boxDepth:  { type: Number, default: 80 },
  coordSystem: { type: String, default: 'xyz' },  // 'xyz' | 'rz'
});

// ── 暴露端到端渲染时间给父组件 ──────────────────────────────────────────────
const emit = defineEmits(['render-time']);

// ─── Refs ───────────────────────────────────────────────────────────────────
const containerEl = ref(null);
const chartEl     = ref(null);

// ─── Derived state ──────────────────────────────────────────────────────────
const hasData = computed(() => props.points.length > 0);
const nPts    = computed(() => props.points.length.toLocaleString());

// ─── ECharts instance ───────────────────────────────────────────────────────
let chart = null;
let ro    = null;   // ResizeObserver

/** Jet 色带（与原 GLSL jet 函数一致） */
const JET_COLORS = [
  '#00007f', '#0000ff', '#007fff', '#00ffff',
  '#7fff7f', '#ffff00', '#ff7f00', '#ff0000', '#7f0000',
];

/** 格式化数值 */
const fmt = (v) =>
  (v == null || isNaN(v)) ? '--'
  : (Math.abs(v) < 0.001 || Math.abs(v) >= 1000) ? v.toExponential(2)
  : v.toFixed(4);

/** 构建 ECharts option */
function buildOption(pts) {
  if (!pts || pts.length === 0) return {};

  let vMin = Infinity, vMax = -Infinity;
  const data = pts.map(p => {
    if (p.value < vMin) vMin = p.value;
    if (p.value > vMax) vMax = p.value;
    return [p.x, p.y, p.z, p.value];
  });

  if (vMin === vMax) { vMin -= 0.001; vMax += 0.001; }

  return {
    tooltip: {
      formatter(params) {
        const d = params.data;
        const isRZ = props.coordSystem === 'rz';
        const r = isRZ ? Math.sqrt(d[0]*d[0] + d[1]*d[1]).toFixed(2) : null;
        return `<b>${props.label || '电磁场'}</b><br/>`
             + (isRZ
               ? `r: ${r} mm<br/>z: ${d[2].toFixed(2)} mm<br/>`
               : `x: ${d[0].toFixed(2)} mm<br/>y: ${d[1].toFixed(2)} mm<br/>z: ${d[2].toFixed(2)} mm<br/>`)
             + `${props.label || 'value'}: ${fmt(d[3])} ${props.unit}`;
      },
    },
    visualMap: {
      show: true,
      min: vMin,
      max: vMax,
      calculable: true,
      dimension: 3,
      inRange: { color: JET_COLORS },
      text: [`${fmt(vMax)}`, `${fmt(vMin)}`],
      textStyle: { color: '#94a3b8', fontSize: 10, fontFamily: 'Consolas, "SF Mono", monospace' },
      right: 20,
      top: 'center',
      itemWidth: 14,
      itemHeight: 192,
      textGap: 6,
    },
    grid3D: {
      boxWidth:  props.boxWidth,
      boxHeight: props.boxHeight,
      boxDepth:  props.boxDepth,
      environment: 'none',
      viewControl: {
        autoRotate: false,
        distance: 200,
        alpha: 25,
        beta: 45,
        rotateSensitivity: 2,
        zoomSensitivity: 1.5,
        panSensitivity: 1,
        damping: 0.8,
      },
      light: {
        main:    { intensity: 1.2, shadow: false },
        ambient: { intensity: 0.4 },
      },
      axisLine:    { lineStyle: { color: '#4a6a8a' } },
      axisPointer: { lineStyle: { color: '#4a6a8a' } },
      splitLine:   { lineStyle: { color: 'rgba(74,106,138,0.25)' } },
      axisLabel:   { textStyle: { color: '#94a3b8', fontSize: 10 } },
    },
    xAxis3D: {
      name: props.coordSystem === 'rz' ? 'x(r·cosθ) / mm' : 'x / mm',
      type: 'value',
      nameTextStyle: { color: '#60a5fa', fontSize: 11 },
    },
    yAxis3D: {
      name: props.coordSystem === 'rz' ? 'y(r·sinθ) / mm' : 'y / mm',
      type: 'value',
      nameTextStyle: { color: '#60a5fa', fontSize: 11 },
    },
    zAxis3D: {
      name: 'z / mm',
      type: 'value',
      nameTextStyle: { color: '#60a5fa', fontSize: 11 },
    },
    series: [{
      type: 'scatter3D',
      data,
      symbolSize: 4,
      itemStyle: { borderWidth: 0, opacity: 0.92 },
      emphasis: {
        itemStyle: { color: '#ffffff', borderColor: '#60a5fa', borderWidth: 1 },
      },
    }],
    backgroundColor: 'transparent',
  };
}

/** 初始化 / 更新图表 */
function updateChart() {
  if (!chart || !hasData.value) return;
  const t0 = performance.now();
  chart.setOption(buildOption(props.points), { notMerge: true });
  // RAF：等浏览器提交当前帧，此时 WebGL 绘制指令已全部执行
  requestAnimationFrame(() => {
    const renderMs = Math.round(performance.now() - t0);
    emit('render-time', renderMs);
    console.log(
      `[WebGL3DScatter] ${props.points.length} pts → WebGL render: ${renderMs} ms`
    );
  });
}

// ─── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await nextTick();
  if (!chartEl.value) return;

  chart = echarts.init(chartEl.value, null, { renderer: 'canvas' });
  updateChart();

  ro = new ResizeObserver(() => chart && chart.resize());
  ro.observe(containerEl.value);
});

onBeforeUnmount(() => {
  if (ro) { ro.disconnect(); ro = null; }
  if (chart) { chart.dispose(); chart = null; }
});

watch(() => props.points, () => updateChart(), { deep: false });
</script>

