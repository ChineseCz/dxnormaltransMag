<template>
  <div class="p-4 text-white">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column -->
      <div>
        <!-- Contact Info -->
        <div class="bg-gray-800 p-6 rounded-lg">
          <h2 class="text-2xl font-bold mb-4">联系信息</h2>
          <p class="text-gray-400 mb-2">
            <el-icon><OfficeBuilding /></el-icon> 官网: <a href="#" class="text-blue-400 hover:underline">http://www.example.com</a>
          </p>
          <p class="text-gray-400 mb-2">
            <el-icon><Message /></el-icon> 微信: <span class="ml-2">YourWeChat</span>
          </p>
          <p class="text-gray-400">
            <el-icon><Money /></el-icon> 支付宝: <span class="ml-2">your.alipay@example.com</span>
          </p>
        </div>
      </div>

      <!-- Right Column -->
      <div>
        <!-- Tech Stack -->
        <div class="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 class="text-2xl font-bold mb-4">技术选型</h2>
          <div class="flex flex-wrap gap-4">
            <div class="w-1/2">
              <h3 class="font-semibold">后端技术</h3>
              <ul class="list-disc list-inside text-gray-400">
                <li>Python</li>
                <li>PyTorch</li>
                <li>FastAPI</li>
                <li>Pandas</li>
              </ul>
            </div>
            <div class="w-1/2">
              <h3 class="font-semibold">前端技术</h3>
              <ul class="list-disc list-inside text-gray-400">
                <li>Vue 3</li>
                <li>Vite</li>
                <li>Element Plus</li>
                <li>Tailwind CSS</li>
                <li>ECharts</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Update Log -->
        <div class="bg-gray-800 p-6 rounded-lg">
          <h2 class="text-2xl font-bold mb-4">更新日志</h2>
          <ul class="text-gray-400 space-y-2">
            <li v-for="log in updateLogs" :key="log.version" class="flex justify-between items-center hover:bg-gray-700 p-2 rounded">
              <span>{{ log.version }} - {{ log.date }}</span>
              <el-icon class="cursor-pointer"><ArrowRight /></el-icon>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { OfficeBuilding, Message, Money, ArrowRight } from '@element-plus/icons-vue';

const updateLogs = ref([
  { version: 'v1.0.0', date: '2026-03-13' },
  { version: 'v0.9.0', date: '2026-02-28' },
  { version: 'v0.8.0', date: '2026-02-15' },
]);

const goToDocs = () => {
  console.log('Navigating to documentation...');
};

const goToGithub = () => {
  console.log('Navigating to GitHub...');
};
</script>

<style scoped>
/* Scoped styles for the dashboard */
</style>
