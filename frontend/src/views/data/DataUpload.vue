<template>
  <div class="p-6 space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#0891b2,#06b6d4); box-shadow:0 0 20px rgba(8,145,178,0.4);">
            <el-icon size="20" style="color:white;"><Upload /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#22d3ee,#67e8f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            数据上传与智能校验
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">将仿真物理场文件上传至指定数据集</p>
      </div>
    </div>

    <!-- Dataset Selector -->
    <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <DatasetSelector ref="selectorRef" @change="onDatasetChange" />
      <p v-if="!activeDataset" class="text-yellow-500/80 text-xs mt-2">
        ⚠ 请先在「数据集管理」中创建一个数据集，再进行数据上传
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6" v-if="activeDataset">
      <!-- Upload Section -->
      <el-card class="col-span-2 bg-gray-800 border-gray-700 text-white shadow-xl">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold">数据源导入 — {{ activeDataset.name }}</span>
            <el-tag type="info">支持多文件并行上传</el-tag>
          </div>
        </template>

        <!-- Role selector for this batch -->
        <div class="flex items-center gap-4 mb-4 p-3 rounded-lg" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.4);">
          <span class="text-slate-400 text-xs font-semibold flex-shrink-0">文件角色：</span>
          <el-radio-group v-model="uploadRole" size="small">
            <el-radio-button value="output">
              <span class="text-xs">📊 输出场数据</span>
            </el-radio-button>
            <el-radio-button value="input">
              <span class="text-xs">📈 输入激励量</span>
            </el-radio-button>
            <el-radio-button value="coordinate">
              <span class="text-xs">📍 坐标文件</span>
            </el-radio-button>
          </el-radio-group>
          <template v-if="uploadRole === 'input' && activeDataset.inputVariables?.length">
            <span class="text-slate-500 text-xs">对应变量：</span>
            <el-select v-model="uploadVarIndex" size="small" style="width:180px;" placeholder="选择输入变量">
              <el-option v-for="(v, i) in activeDataset.inputVariables" :key="i"
                         :label="`#${i} ${v.name} (${v.unit})`" :value="i" />
            </el-select>
          </template>
        </div>

        <el-upload
          class="upload-demo"
          drag
          :action="uploadUrl"
          name="file"
          multiple
          :data="uploadFormData"
          :on-success="handleSuccess"
          :on-error="handleError"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text text-gray-400">
            将物理场仿真文件 (.txt) 拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip text-gray-500">
              {{ uploadTip }}
            </div>
          </template>
        </el-upload>
      </el-card>

      <!-- Analysis Panel -->
      <el-card class="bg-gray-800 border-gray-700 text-white shadow-xl">
        <template #header>
          <span class="font-bold text-blue-400">数据集概况</span>
        </template>
        <div class="space-y-4">
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">设备类型</span>
            <el-tag size="small">{{ deviceLabel(activeDataset.deviceType) }}</el-tag>
          </div>
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">物理场</span>
            <el-tag size="small" :type="fieldTag(activeDataset.fieldType)">{{ fieldLabel(activeDataset.fieldType) }}</el-tag>
          </div>
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">输入变量数</span>
            <span class="text-blue-300 text-xs font-mono">{{ (activeDataset.inputVariables || []).length }} 维</span>
          </div>
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">空间测点</span>
            <span class="text-emerald-300 text-xs font-mono">{{ activeDataset.outputVariable?.spatialPoints || '待上传后自动检测' }}</span>
          </div>
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">时间步长</span>
            <span class="text-purple-300 text-xs font-mono">{{ activeDataset.timeStep }}s</span>
          </div>
          <div class="flex justify-between items-center bg-gray-900 p-2 rounded">
            <span class="text-xs text-gray-400">已上传文件</span>
            <span class="text-yellow-300 text-xs font-mono">{{ (activeDataset.files || []).length }} 个</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- File List -->
    <div v-if="activeDataset && activeDataset.files?.length" class="mt-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-white">已上传文件</h2>
      </div>
      <el-table :data="activeDataset.files" style="width: 100%" class="custom-table">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <el-select v-model="row.role" size="small" style="width:130px;"
                       @change="updateFileRole(row)">
              <el-option label="📊 输出场" value="output" />
              <el-option label="📈 输入量" value="input" />
              <el-option label="📍 坐标" value="coordinate" />
              <el-option label="❓ 未分配" value="unknown" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="变量映射" width="180">
          <template #default="{ row }">
            <el-select v-if="row.role === 'input'" v-model="row.variableIndex" size="small"
                       style="width:160px;" placeholder="选择变量" @change="updateFileRole(row)">
              <el-option v-for="(v, i) in activeDataset.inputVariables" :key="i"
                         :label="`#${i} ${v.name}`" :value="i" />
            </el-select>
            <span v-else class="text-slate-600 text-xs">—</span>
          </template>
        </el-table-column>
        <el-table-column label="维度" width="120">
          <template #default="{ row }">
            <span class="text-slate-400 text-xs font-mono">
              {{ row.analysis?.rows || '?' }} × {{ row.analysis?.cols || '?' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="uploadTime" label="上传时间" width="170" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="danger" plain @click="handleDeleteFile(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { UploadFilled, Upload } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import DatasetSelector from '../../components/DatasetSelector.vue';

const API = 'http://127.0.0.1:5000/api/dataset';

const selectorRef = ref(null);
const activeDataset = ref(null);
const uploadRole = ref('output');
const uploadVarIndex = ref(0);

const DEVICE_MAP = { transformer:'变压器', reactor:'电抗器', motor:'电机', gis:'GIS', cable:'电缆', busbar:'母线', other:'其他' };
const FIELD_MAP = { magnetic:{l:'磁场',t:''}, temperature:{l:'温度场',t:'warning'}, stress:{l:'应力场',t:'danger'}, electric:{l:'电场',t:'success'}, flow:{l:'流场',t:'info'}, other:{l:'其他',t:'info'} };
const deviceLabel = (t) => DEVICE_MAP[t] || t;
const fieldLabel = (t) => FIELD_MAP[t]?.l || t;
const fieldTag = (t) => FIELD_MAP[t]?.t || 'info';

const uploadUrl = computed(() =>
  activeDataset.value ? `${API}/${activeDataset.value.id}/upload` : ''
);

const uploadFormData = computed(() => ({
  role: uploadRole.value,
  variableIndex: uploadRole.value === 'input' ? String(uploadVarIndex.value) : '',
}));

const uploadTip = computed(() => {
  if (!activeDataset.value) return '';
  const ds = activeDataset.value;
  if (uploadRole.value === 'output') {
    return `输出场文件格式：每行一个空间点，前 ${ds.coordCols || 3} 列为坐标，后续列为各时间步的场值`;
  } else if (uploadRole.value === 'input') {
    const v = ds.inputVariables?.[uploadVarIndex.value];
    return v ? `输入文件：列0=时间，列1=${v.name}(${v.unit}) 的瞬时值` : '请先选择对应的输入变量';
  }
  return '坐标文件：每行一个空间点的 (x, y, z) 坐标';
});

function onDatasetChange(ds) {
  activeDataset.value = ds;
}

async function handleSuccess(response, file) {
  ElMessage.success(`${file.name} 上传成功`);
  await refreshDataset();
}

function handleError(err, file) {
  ElMessage.error(`${file.name} 上传失败`);
}

async function refreshDataset() {
  if (!activeDataset.value) return;
  try {
    const r = await fetch(`${API}/${activeDataset.value.id}`);
    const d = await r.json();
    activeDataset.value = d.dataset;
  } catch { /* ignore */ }
}

async function updateFileRole(row) {
  if (!activeDataset.value) return;
  try {
    await fetch(`${API}/${activeDataset.value.id}/files/${encodeURIComponent(row.filename)}/role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: row.role, variableIndex: row.variableIndex }),
    });
  } catch { /* ignore */ }
}

async function handleDeleteFile(row) {
  if (!activeDataset.value) return;
  try {
    await fetch(`${API}/${activeDataset.value.id}/files/${encodeURIComponent(row.filename)}`, { method: 'DELETE' });
    ElMessage.warning(`已删除 ${row.filename}`);
    await refreshDataset();
  } catch { /* ignore */ }
}
</script>

<style scoped>
.custom-table { background-color: #1f2937; color: white; }
:deep(.el-table) {
  --el-table-bg-color: #1f2937;
  --el-table-tr-bg-color: #1f2937;
  --el-table-header-bg-color: #374151;
  --el-table-text-color: #e5e7eb;
  --el-table-header-text-color: #f3f4f6;
  --el-table-border-color: #4b5563;
}
.upload-demo :deep(.el-upload-dragger) { background-color: #1f2937; border-color: #4b5563; }
.upload-demo :deep(.el-upload-dragger:hover) { border-color: #409eff; }
</style>
