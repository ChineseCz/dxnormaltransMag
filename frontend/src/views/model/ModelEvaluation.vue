<template>
  <div class="p-6 space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#059669,#10b981); box-shadow:0 0 20px rgba(16,185,129,0.4);">
            <el-icon size="20" style="color:white;"><TrendCharts /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#34d399,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            模型结果评估
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">模型预测精度可视化分析与误差评估</p>
      </div>
      <el-dropdown>
        <el-button type="primary">
          更新评估模型: {{ selectedModel }}<el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="m in models" :key="m" @click="selectedModel = m">{{ m }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 电磁场分布对比 -->
      <el-card class="bg-gray-800 border-gray-700" header="电磁场预测值 vs 真实值对比 (1241 点)">
        <div class="h-[350px]">
          <v-chart :option="fieldComparisonOption" autoresize />
        </div>
      </el-card>

      <!-- 误差分布 -->
      <el-card class="bg-gray-800 border-gray-700" header="预测误差分布 (Error Distribution)">
        <div class="h-[350px]">
          <v-chart :option="errorDistOption" autoresize />
        </div>
      </el-card>

      <!-- 核心指标看板 -->
      <el-card class="md:col-span-2 bg-gray-800 border-gray-700 shadow-lg">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon class="text-purple-400"><DataLine /></el-icon>
            <span class="text-white font-bold">全量模型评价指标 (Global Metrics)</span>
          </div>
        </template>
        <el-descriptions :column="4" border class="custom-descriptions">
          <el-descriptions-item label="Mean Squared Error (MSE)">
            <span class="text-blue-400 font-bold font-mono">2.45e-5</span>
          </el-descriptions-item>
          <el-descriptions-item label="Mean Absolute Error (MAE)">
            <span class="text-green-400 font-bold">1.82e-3</span>
          </el-descriptions-item>
          <el-descriptions-item label="R² Score">
            <span class="text-purple-400 font-bold">0.9982</span>
          </el-descriptions-item>
          <el-descriptions-item label="Training Time">
            <span class="text-yellow-400 font-bold">142.5s</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ArrowDown, TrendCharts } from '@element-plus/icons-vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent]);

const selectedModel = ref('DNN_2023-03-13.pth');
const models = ['DNN_2023-03-13.pth', 'DNN_2023-03-12.pth'];

// 模拟电磁场对比数据 (取 50 个点展示)
const points = Array.from({ length: 50 }, (_, i) => i);
const realValues = points.map(p => Math.sin(p / 5) * 5 + 10);
const predValues = realValues.map(v => v + (Math.random() - 0.5) * 0.4);

const fieldComparisonOption = ref({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis' },
  legend: { textStyle: { color: '#94a3b8' } },
  grid: { top: '10%', left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: points, axisLabel: { color: '#64748b' } },
  yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#334155' } } },
  series: [
    { name: '实际电磁场 (Real)', type: 'line', data: realValues, smooth: true, lineStyle: { width: 3, color: '#10b981' } },
    { name: '预测电磁场 (Pred)', type: 'line', data: predValues, lineStyle: { type: 'dashed', color: '#3b82f6' } }
  ]
});

const errorDistOption = ref({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'value', name: 'Error', axisLabel: { color: '#64748b' } },
  yAxis: { type: 'value', name: 'Frequency', axisLabel: { color: '#64748b' }, splitLine: { show: false } },
  series: [{
    type: 'bar',
    data: Array.from({ length: 15 }, () => Math.floor(Math.random() * 20)),
    itemStyle: { color: '#ef4444' }
  }]
});
</script>

<style scoped>
.custom-descriptions :deep(.el-descriptions__label) {
  background-color: #1a202c !important;
  color: #94a3b8 !important;
}
.custom-descriptions :deep(.el-descriptions__content) {
  background-color: #111827 !important;
  color: #f3f4f6;
}
</style>
