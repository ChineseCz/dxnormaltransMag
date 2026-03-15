<template>
  <div class="p-6 space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-white">模型仓库</h1>
        <p class="text-gray-400 text-sm mt-1">管理已保存的 PyTorch 模型权重文件 (.pth)</p>
      </div>
      <el-button type="primary" @click="fetchModels">
        <el-icon class="mr-1"><Refresh /></el-icon>刷新列表
      </el-button>
    </div>

    <el-card class="bg-gray-800 border-gray-700">
      <el-table :data="tableData" style="width: 100%" class="custom-table" v-loading="loading">
        <el-table-column label="模型名称" min-width="250">
          <template #default="scope">
            <div class="flex items-center gap-2">
              <el-icon class="text-yellow-500"><Box /></el-icon>
              <span class="font-mono text-blue-400">{{ scope.row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.name.split('_')[0] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120" />
        <el-table-column prop="date" label="创建时间" width="200" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button-group>
              <el-button size="small" type="primary" plain @click="downloadModel(scope.row)">下载</el-button>
              <el-button size="small" type="success" plain @click="deployModel(scope.row)">激活</el-button>
              <el-button size="small" type="danger" plain @click="deleteModel(scope.row)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模型详情面板 -->
    <el-drawer v-model="drawer" title="模型详细信息" size="40%">
      <div v-if="selectedModel" class="p-4 space-y-4">
        <div class="p-4 bg-gray-900 rounded border border-gray-700 font-mono text-xs text-green-400">
          <pre>{{ selectedModel.meta }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Refresh, Box } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';

const loading = ref(false);
const drawer = ref(false);
const selectedModel = ref(null);

const tableData = ref([
  { name: 'DNN_2023-03-13-10-55-54.pth', size: '1.2MB', date: '2023-03-13 10:55', meta: 'Hidden Layers: [16, 32, 64]\nLR: 1e-4\nBatch: 16' },
  { name: 'DNN_2023-03-12-14-20-11.pth', size: '1.2MB', date: '2023-03-12 14:20', meta: 'Hidden Layers: [32, 64, 128]\nLR: 5e-5\nBatch: 32' }
]);

const fetchModels = () => {
  loading.value = true;
  setTimeout(() => { loading.value = false; }, 500);
};

const deleteModel = (row) => {
  ElMessageBox.confirm(`确定要删除模型 ${row.name} 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('模型已删除');
  });
};

const deployModel = (row) => {
  ElMessage.success({
    message: `模型 ${row.name} 已成功激活，将用于实时预测模块`,
    duration: 3000
  });
};

const downloadModel = (row) => {
  ElMessage.info(`开始准备下载 ${row.name}...`);
};

onMounted(fetchModels);
</script>

<style scoped>
.custom-table {
  --el-table-border-color: #374151;
  --el-table-header-bg-color: #1f2937;
  --el-table-bg-color: #111827;
  --el-table-tr-bg-color: transparent;
  --el-table-header-text-color: #94a3b8;
  --el-table-text-color: #e5e7eb;
}
:deep(.el-table__row:hover > td) {
  background-color: #1f2937 !important;
}
</style>
