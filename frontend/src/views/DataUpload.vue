<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6 text-white">数据上传与智能校验</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <!-- Upload Section -->
      <el-card class="col-span-2 bg-gray-800 border-gray-700 text-white shadow-xl">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold">数据源导入 (Raw Data Source)</span>
            <el-tag type="info">支持多文件并行上传</el-tag>
          </div>
        </template>
        <el-upload
          class="upload-demo"
          drag
          action="http://127.0.0.1:5000/api/data/upload/raw"
          name="file"
          multiple
          :on-success="handleSuccess"
          :on-error="handleError"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text text-gray-400">
            将物理场仿真文件 (.txt) 拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip text-gray-500">
              系统将自动识别：磁场分布件 (mag-*)、电压电流件 (prim/sec-*)
            </div>
          </template>
        </el-upload>
      </el-card>

      <!-- Real-time Statistics Section -->
      <el-card class="bg-gray-800 border-gray-700 text-white shadow-xl">
        <template #header>
          <span class="font-bold text-blue-400">数据质量预评估</span>
        </template>
        <div v-if="analysisStats" class="space-y-4">
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">样本一致性</span>
            <el-tag size="small" :type="analysisStats.consistency === '良好' ? 'success' : 'warning'">
              {{ analysisStats.consistency }}
            </el-tag>
          </div>
          <div class="space-y-1">
            <div class="text-xs text-gray-500">时间步长匹配度</div>
            <el-progress :percentage="analysisStats.timeMatch" :color="customColors" />
          </div>
          <div class="pt-2 border-t border-gray-700">
            <div class="flex justify-between text-xs mb-1">
              <span>测点规模:</span>
              <span class="text-blue-300">{{ analysisStats.points }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span>预估周期数:</span>
              <span class="text-blue-300">{{ analysisStats.cycles }}</span>
            </div>
          </div>
        </div>
        <div v-else class="h-full flex flex-col items-center justify-center text-gray-600 italic py-10">
          <el-icon size="40"><Histogram /></el-icon>
          <p class="mt-2 text-xs">等待数据导入分析...</p>
        </div>
      </el-card>
    </div>

    <div class="mt-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-white">已录入数据集治理仓</h2>
        <el-button-group>
          <el-button type="primary" size="small" plain>全部校验</el-button>
          <el-button type="danger" size="small" plain>清除异常项</el-button>
        </el-button-group>
      </div>
      <el-table :data="fileList" style="width: 100%" class="custom-table">
        <el-table-column prop="name" label="文件名" />
        <el-table-column prop="size" label="大小" />
        <el-table-column prop="uploadTime" label="上传时间" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { UploadFilled, Histogram } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const fileList = ref([
  { name: 'mag-100-10k-50-0.2.txt', size: '1.2MB', uploadTime: '2025-03-24 10:00:00', status: 'normal' },
  { name: 'primvol-100-10k-50-0.2.txt', size: '0.5MB', uploadTime: '2025-03-24 10:05:00', status: 'normal' }
]);

const analysisStats = ref(null);

const customColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 },
];

const handleSuccess = (response, file) => {
  ElMessage.success(`${file.name} 上传并智能分析成功`);

  // 更新统计面板为真实的后端分析数据
  if (response.analysis) {
    analysisStats.value = {
      consistency: response.analysis.is_smooth ? '良好' : '存在跳变',
      timeMatch: 100.0,
      points: response.analysis.rows,
      cycles: (response.analysis.cols - 3) / 20 // 假设 20 点一周期
    };
  }

  // 将文件信息加入列表
  fileList.value.unshift({
    name: file.name,
    size: (file.size / 1024 / 1024).toFixed(2) + 'MB',
    uploadTime: new Date().toLocaleString(),
    status: response.analysis.is_smooth ? 'normal' : 'warning'
  });
};

const handleError = (err, file) => {
  ElMessage.error(`${file.name} 上传失败，请检查后端服务是否启动。`);
};

const handleDelete = (row) => {
  fileList.value = fileList.value.filter(item => item.name !== row.name);
  ElMessage.warning(`已从当前列表移除 ${row.name}`);
};
</script>

<style scoped>
.custom-table {
  background-color: #1f2937;
  color: white;
}
:deep(.el-table) {
  --el-table-bg-color: #1f2937;
  --el-table-tr-bg-color: #1f2937;
  --el-table-header-bg-color: #374151;
  --el-table-text-color: #e5e7eb;
  --el-table-header-text-color: #f3f4f6;
  --el-table-border-color: #4b5563;
}
.upload-demo :deep(.el-upload-dragger) {
  background-color: #1f2937;
  border-color: #4b5563;
}
.upload-demo :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}
</style>
