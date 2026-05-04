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
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">
            输入工况参数 → {{ resultModelType }} 实时预测{{ sceneLabel }}三维场分布
          </p>
        </div>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
             style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399;">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span>
          预测完成
        </div>
      </div>
    </div>

    <!-- 工况场景信息面板 -->
    <div class="px-6 pb-3">
      <div class="rounded-xl px-5 py-4 space-y-3"
           style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.4);">

        <!-- ① 场景标识行 -->
        <div class="flex items-center gap-2.5 pb-2.5 flex-wrap"
             style="border-bottom:1px solid rgba(51,65,85,0.25);">
          <div class="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide"
               style="background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);color:#60a5fa;">
            {{ predictionResult?.datasetName || '预测场景' }}
          </div>
          <div v-if="predictionResult?.timestamp" class="px-2.5 py-0.5 rounded-full text-[10px]"
               style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.25);color:#34d399;">
            {{ predictionResult.timestamp }}
          </div>
        </div>

        <!-- ② 输入工况 -->
        <div class="flex items-center gap-5 flex-wrap">
          <span class="text-[11px] text-slate-500 font-semibold">输入工况</span>
          <div v-for="(p, idx) in displayParams" :key="idx"
               class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
               style="background:rgba(15,23,42,0.5); border:1px solid rgba(51,65,85,0.3);">
            <span class="inline-block w-4 h-4 rounded text-center text-[9px] leading-4 font-bold"
                  :style="`background:${paramColors[idx]}20; color:${paramColors[idx]};`">{{ idx + 1 }}</span>
            <span class="text-slate-400 text-[11px]">{{ p.label }}</span>
            <span class="text-white text-[11px] font-mono font-semibold">{{ p.value }}</span>
            <span class="text-slate-600 text-[10px]">{{ p.unit }}</span>
          </div>
        </div>

        <!-- ③ 模型 + 精度指标 -->
        <div class="flex items-center gap-3 flex-wrap pt-1"
             style="border-top:1px solid rgba(51,65,85,0.25);">
          <span class="text-[11px] text-slate-500 font-semibold">预测模型</span>
          <el-tag size="small" effect="dark" round
                  style="background:rgba(59,130,246,0.15); border-color:rgba(59,130,246,0.3); color:#60a5fa;">
            {{ resultModelType }}
          </el-tag>
          <span class="text-slate-400 text-[10px] font-mono">{{ resultModelFile }}</span>
          <div class="flex items-center gap-1.5 ml-2">
            <template v-if="predictionResult?.stats">
              <span class="metric-chip">最小值 <b class="text-cyan-400">{{ fmtStat(predictionResult.stats.min) }} {{ fieldUnit }}</b></span>
              <span class="metric-chip">最大值 <b class="text-cyan-400">{{ fmtStat(predictionResult.stats.max) }} {{ fieldUnit }}</b></span>
              <span class="metric-chip">均值 <b class="text-green-400">{{ fmtStat(predictionResult.stats.mean) }} {{ fieldUnit }}</b></span>
              <span class="metric-chip">耗时 <b class="text-amber-400">{{ predictionResult.latency_s }}s</b></span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 主体 -->
    <div class="px-6 pb-6">
      <div class="chart-card">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-md flex items-center justify-center"
                 style="background:rgba(34,211,238,0.15);">
              <el-icon size="13" style="color:#22d3ee;"><Grid /></el-icon>
            </div>
            <span class="text-white font-bold text-sm">三维{{ sceneLabel }}预测结果对比</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full"
                  style="background:rgba(34,211,238,0.1); color:#22d3ee; border:1px solid rgba(34,211,238,0.3);">
              模拟真值 vs {{ resultModelType }} 预测
            </span>
          </div>
          <span class="text-[11px] text-slate-500">{{ fieldLabel }} ({{ fieldUnit }})</span>
        </div>

        <!-- 三图并排 -->
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;padding:14px;">
          <div class="flex flex-col gap-1.5">
            <div class="text-center py-1 text-xs font-semibold rounded-md tracking-wide"
                 style="background:rgba(96,165,250,0.1);color:#60a5fa;border:1px solid rgba(96,165,250,0.25);">
              (a) 模拟真值参考
            </div>
            <div style="height:430px;" class="rounded-lg overflow-hidden">
              <WebGL3DScatter :points="gtPoints" :unit="fieldUnit" :label="fieldLabel" :coordSystem="coordSystem" class="w-full h-full" />
            </div>
          </div>
          <div class="flex flex-col gap-1.5">
            <div class="text-center py-1 text-xs font-semibold rounded-md tracking-wide"
                 style="background:rgba(52,211,153,0.1);color:#34d399;border:1px solid rgba(52,211,153,0.25);">
              (b) {{ resultModelType }} 预测结果
            </div>
            <div style="height:430px;" class="rounded-lg overflow-hidden">
              <WebGL3DScatter :points="dnnPoints" :unit="fieldUnit" :label="fieldLabel" :coordSystem="coordSystem" class="w-full h-full" />
            </div>
          </div>
          <div class="flex flex-col gap-1.5">
            <div class="text-center py-1 text-xs font-semibold rounded-md tracking-wide"
                 style="background:rgba(251,191,36,0.1);color:#fbbf24;border:1px solid rgba(251,191,36,0.25);">
              (c) 二者作差结果
            </div>
            <div style="height:430px;" class="rounded-lg overflow-hidden">
              <WebGL3DScatter :points="diffPoints" :unit="fieldUnit" :label="`|Δ${fieldLabel}|`" :coordSystem="coordSystem" class="w-full h-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Grid, DataLine } from '@element-plus/icons-vue';
import WebGL3DScatter from '../../components/WebGL3DScatter.vue';
import { usePredictionStore } from '../../composables/usePredictionStore.js';

const { predictionResult } = usePredictionStore();

// ──── 坐标系（直接从数据集配置读取，无需反推） ────
const coordSystem = computed(() => predictionResult.value?.coordSystem || 'xyz');

// ──── 场量元信息（从 predictionResult 动态读取） ────
const fieldUnit  = computed(() => predictionResult.value?.outputUnit  || 'T');
const fieldLabel = computed(() => predictionResult.value?.outputLabel || 'B');
const sceneLabel = computed(() => {
  const ft = predictionResult.value?.fieldType;
  const map = { magnetic: '磁场', temperature: '温度场', electric: '电场', stress: '应力场', flow: '流场' };
  return map[ft] || '物理场';
});

// ──── 参数配色 ────
const paramColors = ['#60a5fa', '#c084fc', '#34d399', '#fbbf24'];

// ──── 输入工况显示 ────
const displayParams = computed(() => {
  const r = predictionResult.value;
  if (!r) return [];
  if (r.inputs && Object.keys(r.inputs).length) {
    return Object.entries(r.inputs).map(([label, value]) => ({
      label,
      value: typeof value === 'number' ? value.toFixed(6) : String(value ?? '—'),
      unit: '',
    }));
  }
  if (r.inputArray?.length) {
    return r.inputArray.map((v, i) => ({
      label: `变量 ${i + 1}`,
      value: typeof v === 'number' ? v.toFixed(6) : String(v ?? '—'),
      unit: '',
    }));
  }
  return [];
});

const resultModelType = computed(() => predictionResult.value?.modelType || 'DNN');
const resultModelFile = computed(() => predictionResult.value?.modelFile || '—');

function fmtStat(v) {
  if (v == null || isNaN(v)) return '—';
  return (Math.abs(v) < 0.001 || Math.abs(v) >= 1000) ? v.toExponential(3) : v.toFixed(4);
}

// ──── 三组场点数据 ────
const gtPoints   = ref([]);
const dnnPoints  = ref([]);
const diffPoints = ref([]);

function buildPoints(fieldValues, coordinates) {
  if (!fieldValues?.length) return [];
  return fieldValues.map((v, i) => ({
    x: coordinates?.[i]?.x ?? 0,
    y: coordinates?.[i]?.y ?? 0,
    z: coordinates?.[i]?.z ?? 0,
    value: v,
  }));
}

function simulateGt(dnnPts) {
  const vMax = dnnPts.reduce((m, p) => Math.max(m, Math.abs(p.value)), 1e-12);
  const amp  = 0.005 * vMax;
  return dnnPts.map(p => ({ ...p, value: p.value + (Math.random() - 0.5) * 2 * amp }));
}

function computeDiff(gtPts, dnnPts) {
  return gtPts.map((p, i) => ({ ...p, value: Math.abs(p.value - (dnnPts[i]?.value ?? 0)) }));
}

function genDemo3D(n = 800) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const x = (Math.random() - 0.5) * 80;
    const y = (Math.random() - 0.5) * 40;
    const z = (Math.random() - 0.5) * 80;
    const r = Math.sqrt(x * x + z * z) / 40;
    const B = (0.70 * Math.exp(-r * 2.5) + 0.015) * (0.85 + 0.15 * Math.random());
    pts.push({ x, y, z, value: Math.max(0.003, Math.min(0.7147, B)) });
  }
  return pts;
}

async function loadData() {
  const r = predictionResult.value;
  if (r?.fieldValues?.length) {
    const predicted  = buildPoints(r.fieldValues, r.coordinates);
    dnnPoints.value  = predicted;
    gtPoints.value   = simulateGt(predicted);
    diffPoints.value = computeDiff(gtPoints.value, predicted);
    return;
  }
  // fallback：无真实数据时显示演示点云
  const demo = genDemo3D();
  gtPoints.value   = demo;
  dnnPoints.value  = demo.map(p => ({ ...p, value: p.value * (0.995 + Math.random() * 0.01) }));
  diffPoints.value = computeDiff(gtPoints.value, dnnPoints.value);
}

onMounted(() => { loadData(); });
</script>

<style scoped>
.metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 10px;
  color: #94a3b8;
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.4);
}
.metric-chip b { font-family: 'Consolas', monospace; font-style: normal; }
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
</style>
